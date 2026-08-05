from .rest import rest_subagent
from .graphql import graphql_subagent
from .grpc import grpc_subagent
from .soap import soap_subagent

__all__ = [
    "rest_subagent",
    "graphql_subagent",
    "grpc_subagent",
    "soap_subagent",
]
