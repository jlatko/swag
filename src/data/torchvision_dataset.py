import argparse

import pytorch_lightning as pl
from torch.utils.data import random_split
from torch.utils.data import DataLoader, Subset
from torchvision import datasets
from src.data.util import get_transformations
from src.data.base_data_module import BaseDataModule, load_and_print_info
from sklearn.model_selection import train_test_split
import numpy as np
from src.util import filter_args_for_fn, get_default_args, fn_defaults_to_argparse

DOWNLOADED_DATA_DIRNAME = BaseDataModule.data_dirname() / "downloaded"


class TorchvisionDataset(BaseDataModule):
    """
    Torchvision datasets wrapped into pytorch lightning
    """
    def __init__(self, args: argparse.Namespace=None) -> None:
        super().__init__(args)
        self.dataset_name = args.dataset_name
        self.data_class = getattr(datasets, self.dataset_name)
        self.data_dir = DOWNLOADED_DATA_DIRNAME
        self.transformation_kwargs = filter_args_for_fn(vars(args), get_transformations)

    @staticmethod
    def add_to_argparse(parser):
        BaseDataModule.add_to_argparse(parser)
        parser.add_argument(
            "--dataset_name", type=str, default='CIFAR10', help="Name of the Torchvision dataset class"
        )
        fn_defaults_to_argparse(get_transformations, parser) # this is ugly, but I don't like argparse propagating that deep
        return parser

    def setup(self, stage=None):
        """Split into train, val, test, and set dims."""
        self.transform_train = get_transformations(train=True, **self.transformation_kwargs)
        self.transform_test = get_transformations(train=False, **self.transformation_kwargs)

        if 'train' in self.data_class.__init__.__code__.co_varnames:
            self.data_train = self.data_class(self.data_dir, train=True, transform=self.transform_train)
            self.data_val = self.data_class(self.data_dir, train=True, transform=self.transform_test)
            # split train/val
            targets = np.array(self.data_train.targets)
            train_idx, val_idx = train_test_split(
                                np.arange(len(targets)),
                                test_size=0.1,
                                shuffle=True,
                                stratify=targets,
                                random_state=0) # seed is important
            self.data_train = Subset(self.data_train, train_idx)
            self.data_val = Subset(self.data_val, val_idx)
            self.data_test = self.data_class(self.data_dir, train=False, transform=self.transform_test)

        else:
            self.data_train = self.data_class(self.data_dir, split='train', transform=self.transform_train)
            self.data_val = self.data_class(self.data_dir, split='val', transform=self.transform_test)
            self.data_test = self.data_class(self.data_dir, split='test', transform=self.transform_test)

    def prepare_data(self):
        self.data_class(self.data_dir, download=True)

    # def train_dataloader(self):
    #     return DataLoader(self.data_train, shuffle=True, batch_size=self.batch_size, num_workers=self.num_workers, pin_memory=True)

    # def val_dataloader(self):
    #     return DataLoader(self.data_val, shuffle=False, batch_size=self.batch_size, num_workers=self.num_workers, pin_memory=True)

    # def test_dataloader(self):
    #     return DataLoader(self.data_test, shuffle=False, batch_size=self.batch_size, num_workers=self.num_workers, pin_memory=True)
    