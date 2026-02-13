#!/usr/bin/env python3

"""
BitcoinCorelient is an asynchronous client for communicating with a Bitcoin Core node via JSON-RPC.
"""

import asyncio
import base64
from typing import Any, Optional

import aiohttp
from dotenv import dotenv_values

config = dotenv_values("env/BitcoinRPC.env")


class BitcoinCoreClient:
    """
    Client async to comunication with Bitcoin Core via JSON-RPC.
    It provides methods to interact with the Bitcoin network, such as getting block information, sending transactions, and more. The client is designed to be used in an asynchronous context, allowing for efficient handling of multiple requests without blocking the main thread.

    Use:
        async with BitcoinCoreClient(...) as client:
            block = await client.get_block_by_hash(block_hash)
    """

    def __init__(
        self,
        rpc_username: Optional[str] = None,
        rpc_password: Optional[str] = None,
        rpc_host: Optional[str] = None,
        rpc_port: Optional[int] = None,
        timeout: Optional[int] = 10,
    ) -> None:
        """
        Initialize the Bitcoin Core Client with credenciais RPC.

        :param rpc_username: Username for RPC authentication
        :type rpc_username: Optional[str]
        :param rpc_password: Password for RPC authentication
        :type rpc_password: Optional[str]
        :param rpc_host: Host address for RPC connection
        :type rpc_host: Optional[str]
        :param rpc_port: Port for RPC connection
        :type rpc_port: Optional[int]
        """
        self._rpc_user = rpc_username or config.get("RPC_USER")
        self._rpc_password = rpc_password or config.get("RPC_PASSWORD")
        self._rpc_host = rpc_host or config.get("RPC_HOST")
        self._rpc_port = rpc_port or int(config.get("RPC_PORT", 8332))  # type: ignore
        self._url = f"http://{self._rpc_host}:{self._rpc_port}"

        # Prepare authentication for header HTTP Basic Auth
        auth_str = f"{self._rpc_user}:{self._rpc_password}"
        # self._auth_header = {"Authorization": f"Basic {auth_str.encode('utf-8').hex()}"}
        self._auth_header = {
            "Authorization": f"Basic {base64.b64encode(auth_str.encode()).decode()}",
            "Content-Type": "application/json",
        }

        self._session: Optional[aiohttp.ClientSession] = None
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    async def __aenter__(self) -> "BitcoinCoreClient":
        """Connect to the Bitcoin RPC server when entering the context."""

        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers=self._auth_header, timeout=self._timeout
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close the connection to the Bitcoin RPC server when exiting the context."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _handle_request(self, method: str, **kwargs) -> dict[str, Any]:
        """
        Internal method to perform an asynchronous RPC call to the Bitcoin Core node.

        :param method: The RPC method to call
        :type method: str
        :param params: The parameters for the RPC call
        :type params: list
        :return: The result of the RPC call
        :rtype: dict[str, Any]
        """
        if not self._session:
            raise RuntimeError(
                "Client session is not initialized. Use 'async with' to manage the connection."
            )

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": [{key: val for key, val in kwargs.items()}] if kwargs else [],
            "id": "miner-python-client",
        }

        print(f"Making RPC call: {method} with params: {kwargs}")

        try:
            async with self._session.post(self._url, json=payload) as response:
                response.raise_for_status()
                result = await response.json()
                if "error" in result and result["error"] is not None:
                    raise RuntimeError(f"RPC Error: {result['error']}")
                return result["result"]
        except aiohttp.ClientError as e:
            raise RuntimeError(f"HTTP error during RPC call: {e}")

    async def getblocktemplate(self, **kwargs) -> dict[str, Any]:
        """
        Get a block template from the Bitcoin Core node.

        :return: A block template for mining
        :rtype: dict[str, Any]
        """

        params = {"rules": ["segwit"]} if not kwargs else kwargs

        return await self._handle_request("getblocktemplate", **params)

    async def getblockcount(self) -> int:
        """
        Get the current block count from the Bitcoin Core node.

        :return: The current block count
        :rtype: int
        """
        result = await self._handle_request("getblockcount")
        if isinstance(result, (int, str)):
            return int(result)
        raise RuntimeError(f"Unexpected result type for getblockcount: {type(result)}")


async def main() -> None:
    async with BitcoinCoreClient() as client:
        try:
            template = await client.getblocktemplate()
            # Analyse the data more important in the template, for example:
            print("--- New Template of Miner ---")
            print(f"Difficulty (Bits): {template['bits']}")
            print(f"Hash Previous: {template['previousblockhash']}")
            print(f"Reward (Coinbase): {template['coinbasevalue']} Satoshis")
            print(f"Number of Transactions: {len(template['transactions'])}")

            # Here, you can iterate in transactions to see the fees
            top_fee = max(tx["fee"] for tx in template["transactions"])
            print(f"Bigger tax found in block: {top_fee} sats")

            # Show the current block count
            bloco_count = await client.getblockcount()
            print(f"Current block count: {bloco_count}")
        except Exception as e:
            print(f"Error fetching block template: {e}")


if __name__ == "__main__":
    asyncio.run(main())
