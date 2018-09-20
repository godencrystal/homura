import torch
from torch.autograd import Variable
from torch import nn
from torch.nn import functional as F
import math

__all__ = ["unet"]


class Block(nn.Module):
    def __init__(self, in_channel, out_channel):
        """
        >>> a = Variable(torch.randn(1, 1, 128, 128))
        >>> encoder = Block(1, 64)
        >>> encoder(a).size()
        torch.Size([1, 64, 128, 128])
        """
        super().__init__()
        self.block = nn.Sequential(nn.Conv2d(in_channel, out_channel, kernel_size=3, padding=1),
                                   nn.BatchNorm2d(out_channel),
                                   nn.ReLU(inplace=True),
                                   nn.Conv2d(out_channel, out_channel,
                                             kernel_size=3, padding=1),
                                   nn.BatchNorm2d(out_channel),
                                   nn.ReLU(inplace=True))

    def forward(self, input):
        return self.block(input)


class UpsampleBlock(nn.Module):
    def __init__(self, in_channel, out_channel, upsample=True):
        """
        >>> a = Variable(torch.randn(1, 1, 128, 128))
        >>> encoder = Block(1, 64)
        >>> encoder(a).size()
        torch.Size([1, 64, 128, 128])
        """
        super().__init__()
        if upsample:
            self.upsample = nn.Sequential(nn.Upsample(scale_factor=2, mode="bilinear"),
                                          nn.Conv2d(in_channel, out_channel, kernel_size=3, padding=1))
        else:
            self.upsample = nn.ConvTranspose2d(in_channel, out_channel, kernel_size=2)
        self.decoder = Block(in_channel, out_channel)

    def forward(self, input, bypass):
        x = self.upsample(input)
        _, _, i_h, i_w = x.shape
        _, _, b_h, b_w = bypass.shape
        pad = (math.ceil((b_w - i_w) / 2), math.floor((b_w - i_w) / 2),
               math.ceil((b_h - i_h) / 2), math.floor((b_h - i_h) / 2))
        x = F.pad(x, pad)
        x = self.decoder(torch.cat([x, bypass], dim=1))
        return x


class DownsampleBlock(Block):
    def forward(self, input):
        input = F.max_pool2d(input, 2, 2)
        return self.block(input)


class UNet(nn.Module):
    def __init__(self, num_classes, input_channels,
                 config=((64, 128, 256, 512, 1024),
                         (1024, 512, 256, 128, 64))):
        """
        UNet, proposed in Ronneberger et al. (2015)
        :param num_classes: number of output classes
        :param input_channels: number of input channels
        >>> unet = UNet(10, 3) # number of classes = 10
        >>> dummy = Variable(torch.randn(1, 3, 128, 128))
        >>> unet(dummy).shape
        torch.Size([1, 10, 128, 128])
        >>> dummy = Variable(torch.randn(1, 3, 427, 640))
        >>> unet(dummy).shape
        torch.Size([1, 10, 427, 640])
        """
        super(UNet, self).__init__()
        encoder_config, decoder_config = config
        encoder_config = list(encoder_config)
        decoder_config = list(decoder_config)
        # zip (3, 64, 128, 256, 512) and (64, 128, 256, 512, 1024)
        # (3, 64), (64, 128), (128, 256), (256, 512), (512, 1024)
        encoder_config = list(zip([input_channels] + encoder_config[:-1], encoder_config))
        # (1024, 512), (512, 256), (256, 128), (128, 64)
        decoder_config = list(zip(decoder_config, decoder_config[1:]))

        self.encoders = nn.ModuleList([Block(*encoder_config[0])] +
                                      [DownsampleBlock(i, j) for i, j in encoder_config[1:]])
        self.decoders = nn.ModuleList([UpsampleBlock(i, j) for i, j in decoder_config])
        self.down_conv1 = nn.Conv2d(64, num_classes, kernel_size=1)
        self.init_parameters()

    def forward(self, input):

        x = [input]
        for enc in self.encoders:
            # [input, enc1(input), enc2(input), enc3(input)]
            x += [enc(x[-1])]
        # enc3(input), (enc2(input), enc(input), input)
        x, *rest = reversed(x)
        for dec, _x in zip(self.decoders, rest):
            # x = dec(enc3(input), enc2(input))
            x = dec(x, _x)

        return self.down_conv1(x)

    def init_parameters(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight)
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()


def unet(num_classes, input_channels=3):
    return UNet(num_classes, input_channels)


if __name__ == "__main__":
    import doctest

    doctest.testmod()