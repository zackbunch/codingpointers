from typing import Any, Optional, List, Dict
import logging

from sonarqube.core import Core
from sonarqube.exceptions import (
    InsufficientPrivilegesException,
    GroupNotFoundException,
    GroupAlreadyExistsException,
    UnexpectedResponseException
)

logger = logging.getLogger(__name__)

class Group:
    """
    A class to interact with the SonarQube user groups API.

    Attributes:
        core (Core): An instance of the Core class to interact with the SonarQube API.
    """

    def __init__(self, core: Core):
        """
        Initialize the Group instance.

        Args:
            core (Core): An instance of the Core class to interact with the SonarQube API.
        """
        self.core = core

    def get_groups(self) -> List[Dict[str, Any]]:
        """
        Get a list of all user groups in SonarQube.

        Returns:
            List[Dict[str, Any]]: A list of user groups.

        Raises:
            InsufficientPrivilegesException: If the user does not have privileges to perform the action.
            UnexpectedResponseException: If the API response is unexpected.
        """
        endpoint = "/api/user_groups/search"
        try:
            response = self.core.get(endpoint=endpoint)
            return response.get("groups", [])
        except Exception as e:
            if "403" in str(e):
                raise InsufficientPrivilegesException("Insufficient privileges to perform this action. Please check the token permissions.")
            else:
                raise UnexpectedResponseException(f"Unexpected response: {str(e)}")

    def get_group_id(self, name: str) -> Optional[str]:
        """
        Get the ID of a user group by name.

        Args:
            name (str): The name of the group to search for.

        Returns:
            Optional[str]: The ID of the group if found, None otherwise.

        Raises:
            InsufficientPrivilegesException: If the user does not have privileges to perform the action.
            UnexpectedResponseException: If the API response is unexpected.
        """
        endpoint = "/api/user_groups/search"
        try:
            response = self.core.get(endpoint=endpoint, params={"q": name})
            groups = response.get("groups", [])
            for group in groups:
                if group.get("name") == name:
                    return group.get("id")
            return None  # Group not found, return None
        except Exception as e:
            if "403" in str(e):
                raise InsufficientPrivilegesException("Insufficient privileges to perform this action. Please check the token permissions.")
            else:
                raise UnexpectedResponseException(f"Unexpected response: {str(e)}")

    def create_group(self, name: str, description: Optional[str] = None) -> Any:
        """
        Create a new user group in SonarQube if it does not already exist.

        Args:
            name (str): The name of the group to create.
            description (str, optional): The description for the new group.

        Returns:
            Any: The response from the SonarQube API.

        Raises:
            GroupAlreadyExistsException: If the group already exists.
            UnexpectedResponseException: If the API response is unexpected.
        """
        group_id = self.get_group_id(name)
        if group_id is not None:
            raise GroupAlreadyExistsException(f"Group '{name}' already exists.")

        endpoint = "/api/user_groups/create"
        data = {"name": name}
        if description:
            data["description"] = description
        logger.debug(f"Creating group with data: {data}")
        try:
            response = self.core.post(endpoint=endpoint, data=data)
        except Exception as e:
            if "already exists" in str(e):
                raise GroupAlreadyExistsException(f"Group '{name}' already exists.")
            else:
                raise UnexpectedResponseException(f"Unexpected response: {str(e)}")
        response["changed"] = True
        return response

    def update_group(self, id: str, name: str) -> Any:
        """
        Update an existing user group in SonarQube if the name is different.

        Args:
            id (str): The ID of the group to update.
            name (str): The new name of the group.

        Returns:
            Any: The response from the SonarQube API.

        Raises:
            GroupNotFoundException: If the group does not exist.
            UnexpectedResponseException: If the API response is unexpected.
        """
        current_id = self.get_group_id(name)
        if current_id == id:
            return {"msg": "Group already has the desired name", "changed": False}

        endpoint = "/api/user_groups/update"
        data = {"id": id, "name": name}
        try:
            response = self.core.post(endpoint=endpoint, data=data)
        except Exception as e:
            raise UnexpectedResponseException(f"Unexpected response: {str(e)}")
        response["changed"] = True
        return response

    def delete_group(self, name: str) -> Any:
        """
        Delete a user group in SonarQube if it exists.

        Args:
            name (str): The name of the group to delete.

        Returns:
            Any: The response from the SonarQube API.

        Raises:
            GroupNotFoundException: If the group does not exist.
            UnexpectedResponseException: If the API response is unexpected.
        """
        group_id = self.get_group_id(name)
        if group_id is None:
            raise GroupNotFoundException(f"Group '{name}' does not exist.")

        endpoint = "/api/user_groups/delete"
        data = {"id": group_id}
        logger.debug(f"Deleting group with id: {group_id}")
        try:
            response = self.core.post(endpoint=endpoint, data=data)
        except Exception as e:
            if "does not exist" in str(e):
                raise GroupNotFoundException(f"Group '{name}' does not exist.")
            else:
                raise UnexpectedResponseException(f"Unexpected response: {str(e)}")
        response["changed"] = True
        return response