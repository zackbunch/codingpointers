import logging
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class Core:
    """
    Core class to interact with the SonarQube API.

    Attributes:
        url (str): Base URL of the SonarQube server.
        session (requests.Session): A Requests session for making HTTP calls.
    """

    def __init__(self, url: str, token: str):
        """
        Initialize the Core instance.

        Args:
            url (str): Base URL of the SonarQube server.
            token (str): Token for API access.
        """
        self.url = url
        self.session = requests.Session()
        self.session.auth = (token, "")

    def endpoint_url(self, endpoint: str) -> str:
        """
        Construct the full URL for a given API endpoint.

        Args:
            endpoint (str): The API endpoint to append to the base URL.

        Returns:
            str: The full URL for the API call.
        """
        return f"{self.url}{endpoint}"

    def call(
        self,
        method: callable,
        endpoint: str,
        expected_status_codes: Optional[List[int]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Make an HTTP call using the provided method, endpoint, and data.

        Args:
            method (callable): The HTTP method to use (e.g., session.get, session.post).
            endpoint (str): The API endpoint to call.
            expected_status_codes (list of int, optional): List of expected status codes. Defaults to None.
            params (dict, optional): Optional query parameters. Defaults to None.
            data (dict, optional): Optional data to pass in the request (as form data). Defaults to None.

        Returns:
            Any: The JSON response from the API.

        Raises:
            Exception: If the HTTP request fails or the response status is an error.
        """
        url = self.endpoint_url(endpoint)
        logger.debug(f"Making request to {url} with params {params} and data {data}")
        try:
            if method == self.session.get:
                response = method(url, params=params)
            else:
                response = method(url, data=data)
            if (
                expected_status_codes
                and response.status_code not in expected_status_codes
            ):
                raise requests.HTTPError(
                    f"Unexpected status code: {response.status_code}", response=response
                )
            response.raise_for_status()
            try:
                return response.json() if response.text else {}
            except ValueError:
                return response.text
        except requests.HTTPError as e:
            error_data = e.response.json() if e.response.text else {}
            logger.error(
                f"HTTP error occurred: {str(e)}, URL: {url}, Data: {params or data}, Error Data: {error_data}"
            )
            raise Exception(
                f"HTTP error occurred: {str(e)}, URL: {url}, Data: {params or data}, Error Data: {error_data}"
            )

    def post(self, endpoint: str, data: Dict[str, Any]) -> Any:
        """
        Send a POST request.

        Args:
            endpoint (str): The API endpoint to call.
            data (dict): The form data to send in the request.

        Returns:
            Any: The JSON response from the API.
        """
        return self.call(
            self.session.post, endpoint, expected_status_codes=[200, 201], data=data
        )

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Send a GET request.

        Args:
            endpoint (str): The API endpoint to call.
            params (dict, optional): The query parameters to send in the request. Defaults to None.

        Returns:
            Any: The JSON response from the API.
        """
        return self.call(
            self.session.get, endpoint, expected_status_codes=[200], params=params
        )

    def put(self, endpoint: str, data: Dict[str, Any]) -> Any:
        """
        Send a PUT request.

        Args:
            endpoint (str): The API endpoint to call.
            data (dict): The form data to send in the request.

        Returns:
            Any: The JSON response from the API.
        """
        return self.call(
            self.session.put, endpoint, expected_status_codes=[200], data=data
        )

    def delete(self, endpoint: str, data: Dict[str, Any]) -> Any:
        """
        Send a DELETE request.

        Args:
            endpoint (str): The API endpoint to call.
            data (dict): The form data to send in the request.

        Returns:
            Any: The JSON response from the API.
        """
        return self.call(self.session.delete, endpoint, data=data)
