# Homura [![CircleCI](https://circleci.com/gh/moskomule/homura/tree/master.svg?style=svg)](https://circleci.com/gh/moskomule/homura/tree/master)

[document](https://moskomule.github.io/homura)

*Homura* is a support tool for research experiments.

🔥🔥🔥🔥 *Homura* (焰) is *flame* or *blaze* in Japanese. 🔥🔥🔥🔥

## Requirements

### minimal requirements

```
Python>=3.6
PyTorch>=1.0
torchvision>=0.2.1
tqdm # automatically installed
```

### optional

```
matplotlib
tensorboardX
visdom
miniargs
colorlog
```

To enable distributed training using Synced BN and FP 16, install apex.

```
git clone https://github.com/NVIDIA/apex.git
cd apex
python setup.py install --cuda_ext --cpp_ext
```

### test

```
pytest .
```

## install

```console
pip install git+https://github.com/moskomule/homura
```

or

```console
git clone https://github.com/moskomule/homura
cd homura; pip install -e .
```


# APIs

## utils

* Device Agnostic
* Useful features

```python
from homura import optim, lr_scheduler
from homura.utils import trainers, callbacks, reporters
from torchvision.models import resnet50
from torch.nn import functional as F

resnet = resnet50()
# model will be registered in the trainer
optimizer = optim.SGD(lr=0.1, momentum=0.9)
# optimizer will be registered in the trainer
scheduler = lr_scheduler.MultiStepLR(milestones=[30,80], gamma=0.1)
# list of callbacks
with reporters.TensorboardReporter([callbacks.AccuracyCallback(), 
                                    callbacks.LossCallback()]) as reporter:
    reporter.enable_report_images(image_keys=["generated", "real"])
    trainer = trainers.SupervisedTrainer(resnet, optimizer, loss_f=F.cross_entropy, 
                                         callbacks=reporter, scheduler=scheduler)
```

Now `iteration` of trainer can be updated as follows,

```python
from homura.utils.containers import Map

def iteration(trainer: Trainer, inputs: Tuple[torch.Tensor]) -> Mapping[torch.Tensor]:
    input, target = trainer.to_device(inputs)
    output = trainer.model(input)
    loss = trainer.loss_f(output, target)
    results = Map(loss=loss, output=output)
    if trainer.is_train:
        trainer.optimizer.zero_grad()
        loss.backward()
        trainer.optimizer.step()
    # registered values can be called in callbacks
    results.user_value = user_value
    return results

SupervisedTrainer.iteration = iteration
# or   
trainer.update_iteration(iteration) 
```

Also, `dict` of models, optimizers, loss functions are supported.

```python
trainer = CustomTrainer({"generator": generator, "discriminator": discriminator},
                        {"generator": gen_opt, "discriminator": dis_opt},
                        {"reconstruction": recon_loss, "generator": gen_loss},
                        **kwargs)
```

## metrics

`homura.metrics` contains domain unspecific metrics such as `recall`.

## modules

`homura.modules` contains domain unspecific modules and functions such as `KeyValAttention`.

## vision

`homura.vision` contains modules specific to CV.


## else

* `homura.debug`: debug tools

# Examples

See [examples](examples).

* [cifar10.py](examples/cifar10.py): training ResNet-20 or WideResNet-28-10 with random crop on CIFAR10
* [imagenet.py](examples/imagenet.py): training a CNN on ImageNet on multi GPUs (single and     multi process)
* [gap.py](examples/gap.py): better implementation of generative adversarial perturbation