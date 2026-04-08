"""Abstract interface for the Server, used to avoid circular imports."""

from abc import ABC, abstractmethod


class ServerInterface(ABC):

    data_dir: str

    @abstractmethod
    def create_group(self, name: str, creator: str):
        raise NotImplementedError

    @abstractmethod
    def remove_group(self, address: str):
        raise NotImplementedError

    @abstractmethod
    def find_group(self, address: str):
        raise NotImplementedError

    @abstractmethod
    def list_group_names(self) -> list[tuple[str, str]]:
        raise NotImplementedError
