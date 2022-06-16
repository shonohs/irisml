import abc
import dataclasses
import logging
import pathlib
import pickle
import typing
import urllib.parse
import azure.core.exceptions
from azure.storage.blob import ContainerClient
from irisml.core.hash_generator import HashGenerator


logger = logging.getLogger(__name__)


def create_storage_manager(url: str):
    is_http = urllib.parse.urlparse(url).scheme in ['http', 'https']
    if is_http:
        return AzureBlobStorageManager(url)
    elif pathlib.Path(url).exists():
        return FileSystemStorageManager(pathlib.Path(url))

    raise ValueError(f"Invalid cache storage URL is provided. {url} If it's local file path, please make sure the path exists on your filesystem.")


class StorageManager(abc.ABC):
    """Access the storage that manages cache"""
    @abc.abstractmethod
    def get_hash(self, paths):
        pass

    @abc.abstractmethod
    def get_contents(self, paths):
        pass

    @abc.abstractmethod
    def put_contents(self, paths, contents, hash_value):
        pass


class AzureBlobStorageManager(StorageManager):
    """Interact with Azure Blob Storage.

    URL to the container must be provided. If the URL doesn't contain SAS token, Managed Identity and Intractive authentication will be used.

    Hash value will be stored in the metadata field of the blob.
    """
    HASH_METADATA_NAME = 'irisml_hash'

    def __init__(self, container_url):
        self._container_url = container_url

    def get_hash(self, paths):
        container_client = ContainerClient.from_container_url(self._container_url)
        blob_client = container_client.get_blob_client('/'.join(paths))
        try:
            properties = blob_client.get_blob_properties()
            hash_value = properties.metadata.get(self.HASH_METADATA_NAME)
            return hash_value
        except azure.core.exceptions.ResourceNotFoundError:
            logger.debug(f"{paths} was not found in the container.")
        return None

    def get_contents(self, paths):
        container_client = ContainerClient.from_container_url(self._container_url)
        try:
            contents = container_client.download_blob('/'.join(paths)).readall()
            return contents
        except azure.core.exceptions.ResourceNotFoundError:
            logger.debug(f"{paths} was not found in the container.")
        return None

    def put_contents(self, paths, contents, hash_value):
        try:
            container_client = ContainerClient.from_container_url(self._container_url)
            container_client.upload_blob('/'.join(paths), contents, metadata={self.HASH_METADATA_NAME: hash_value})
        except Exception as e:
            logger.warning(f"Failed to upload cache {paths} (hash={hash_value}) due to {e}. The error is ignored.")


class FileSystemStorageManager(StorageManager):
    """Use the local filesystem as the cache."""

    def __init__(self, cache_dir: pathlib.Path):
        assert isinstance(cache_dir, pathlib.Path)
        self._cache_dir = cache_dir

    def get_hash(self, paths):
        loaded = pickle.loads(self.get_contents(paths))
        return HashGenerator.calculate_hash(loaded)

    def get_contents(self, paths):
        filepath = self._cache_dir.joinpath(*paths)
        if not filepath.exists():
            return None
        return filepath.read_binary()

    def put_contents(self, paths, contents, hash_value):
        filepath = self._cache_dir.joinpath(*paths)
        if filepath.exists():
            logger.warning(f"Path {filepath} already exists. The new cache is not saved.")
            return
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_bytes(contents)


class CachedOutputs:
    """Used to represent cached outputs so that we can load the contents lazily."""
    def __init__(self, storage_manager, base_paths, outputs_class, hash_values: typing.Dict[str, str]):
        self._storage_manager = storage_manager
        self._paths = base_paths
        self._field_types = {f.name: f.type for f in dataclasses.fields(outputs_class)}
        self._hash_values = hash_values
        self._contents = {}

    def get_hash(self, name: str) -> str:
        assert '.' not in name
        return self._hash_values[name]

    def __getattr__(self, name):
        """Load the actual contents."""
        if name not in self._field_types:
            raise ValueError(f"Unexpected path: {name}")

        if name in self._contents:
            return self._contents[name]

        contents = self._storage_manager.get_contents(self._paths + [name])
        value = pickle.loads(contents)

        if not isinstance(value, self._field_types[name]):
            raise RuntimeError(f"The downloaded cache for {name} has invalid type: {type(value)}. Expected: {self._field_types[name]}")

        # Check the hash value of the downloaded cache.
        current_hash = HashGenerator.calculate_hash(value)
        if current_hash != self._hash_values[name]:
            logger.error(f"Downloaded cache {name} has wrong hash. Expected: {self._hash_values[name]}. Actual: {current_hash}. Ignoring this error.")

        self._contents[name] = value
        return value


class CacheManager:
    def __init__(self, storage_manager):
        self._storage_manager = storage_manager

    def get_cache(self, task_name: str, task_version: str, task_hash: str, outputs_class: dataclasses.dataclass):
        """Try to get the cache for the specified task.

        Args:
            task_name (str): The task name.
            task_version (str): The task version
            task_hash (str): The hash value for the task inputs and config.
            outputs_class (dataclasses.dataclass): The dataclass for the task Outputs.
        Returns:
            CachedOutputs if a cache is found. If not, returns None.
        """
        base_paths = [task_name, task_version, task_hash]
        hash_values = {}
        for field in dataclasses.fields(outputs_class):
            hash_values[field.name] = self._storage_manager.get_hash(base_paths + [field.name])
            assert hash_values[field.name] is None or isinstance(hash_values[field.name], str)

        if not any(hash_values.values()):
            return None

        if not all(hash_values.values()):
            logger.warning(f"Some cache files are missing: {hash_values}")
            return None

        return CachedOutputs(self._storage_manager, base_paths, outputs_class, hash_values)

    def upload_cache(self, task_name: str, task_version: str, task_hash: str, outputs: dataclasses.dataclass):
        base_paths = [task_name, task_version, task_hash]
        for name, value in dataclasses.asdict(outputs).items():
            # This hash_value doesn't match with the actual hash for the contents. See HashGenerator for the detail.
            hash_value = HashGenerator.calculate_hash(value)
            contents = pickle.dumps(value)

            # Double check that the hash is calculated correctly.
            # If this check failed, please check the HashGenerator and __getstate__ attribute of the failed object.
            loaded = pickle.loads(contents)
            loaded_hash_value = HashGenerator.calculate_hash(loaded)
            if hash_value != loaded_hash_value:
                logger.error(f"The object {name} has different hash after serialization. Before: {hash_value}. After: {loaded_hash_value} task: {task_name}")

            self._storage_manager.put_contents(base_paths + [name], contents, hash_value)
