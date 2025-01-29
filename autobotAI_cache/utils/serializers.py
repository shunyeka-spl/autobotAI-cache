import pickle
import json

from autobotAI_cache.core.exceptions import SerializationError


def serialize(data, serializer="pickle"):
    """
    Serialize data using the specified serializer

    :param data: Data to serialize
    :param serializer: Serializer name ('pickle' or 'json')
    :return: Serialized data as bytes
    :raises SerializationError: If serialization fails
    """
    try:
        if serializer == "pickle":
            return pickle.dumps(data)
        elif serializer == "json":
            return json.dumps(data).encode("utf-8")
        else:
            raise ValueError(f"Invalid serializer: {serializer}")
    except Exception as e:
        raise SerializationError(f"Failed to serialize data: {e}")


def deserialize(data, serializer="pickle"):
    """
    Deserialize data using the specified serializer

    :param data: Serialized data
    :param serializer: Serializer name ('pickle' or 'json')
    :return: Deserialized data
    :raises SerializationError: If deserialization fails
    """
    try:
        if serializer == "pickle":
            return pickle.loads(data)
        elif serializer == "json":
            return json.loads(data.decode("utf-8"))
        else:
            raise ValueError(f"Invalid serializer: {serializer}")
    except Exception as e:
        raise SerializationError(f"Failed to deserialize data: {e}")
