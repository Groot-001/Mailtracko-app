from abc import ABC, abstractmethod
from typing import Any


class UploaderInterface(ABC):
    """
    Interface for file uploader adapters.
    """

    @abstractmethod
    async def upload_files(
        self,
        files: list[tuple[str, bytes, str | None]],
    ) -> list[dict[str, Any]]:
        """
        Uploads files and returns their storage metadata.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete_file(
        self,
        storage_key: str,
    ) -> None:
        """
        Deletes a file from external storage.
        """
        raise NotImplementedError