#!/usr/bin/env python3

"""
BitcoinCorelient is an asynchronous client for communicating with a Bitcoin Core node via JSON-RPC.
"""

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

    async def _handle_request(self, method: str, *args, **kwargs) -> dict[str, Any]:
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

        params = list(args) if args else []
        params = [{key: val for key, val in kwargs.items()}] if len(kwargs) else params

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": "miner-python-client",
        }

        # print(f"Preparing RPC call: {method} with args: {args} and kwargs: {kwargs}")
        # print(f"Making RPC call: {method} with params: {payload['params']}")

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

    async def getblock(self, hash: str) -> dict[str, Any]:
        """
        Get a block by its hash from the Bitcoin Core node.

        :param hash: The hash of the block to retrieve
        :type hash: str
        :return: The block information
        :rtype: dict[str, Any]
        """

        params = [hash]

        return await self._handle_request("getblock", *params)

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

    async def getmininginfo(self) -> dict[str, Any]:
        """
        Get info about mining from the Bitcoin Core node.

        Command:
            bitcoin-cli getmininginfo

        :return: The mining information
        :rtype: dict[str, Any]

        Return Example Real Data:
                    {
                        "blocks": 936447,
                        "currentblockweight": 3999798,
                        "currentblocktx": 2804,
                        "bits": "17023c7e",
                        "difficulty": 125864590119494.3,
                        "target": "000000000000000000023c7e0000000000000000000000000000000000000000",
                        "networkhashps": 1.017155175832009e+21,
                        "pooledtx": 7756,
                        "blockmintxfee": 0.00000001,
                        "chain": "main",
                        "next": {
                            "height": 936448,
                            "bits": "17023c7e",
                            "difficulty": 125864590119494.3,
                            "target": "000000000000000000023c7e0000000000000000000000000000000000000000"
                        },
                        "warnings": []
                    }
        """

        return await self._handle_request("getmininginfo")

    async def getdifficulty(self) -> float:
        """
        Get info about difficulty to mine from the Bitcoin Core node.

        :return: The mining difficulty
        :rtype: float

        Return Example Real Data:
            125864590119494.3
        """

        result = await self._handle_request("getdifficulty")
        if isinstance(result, (int, float)):
            return float(result)
        raise RuntimeError(f"Unexpected result type for getdifficulty: {type(result)}")

    async def getnetworkhashps(self, num_blocks: int = 120) -> float:
        """
        Get info about network hash rate from the Bitcoin Core node.

        :param num_blocks: The number of blocks to consider for the network hash rate calculation
        :type num_blocks: int
        :return: The network hash rate
        :rtype: float

        Return Example Real Data:
            1.035436076823005e+21
        """

        result = await self._handle_request("getnetworkhashps", num_blocks)
        if isinstance(result, (int, float)):
            return float(result)
        raise RuntimeError(
            f"Unexpected result type for getnetworkhashps: {type(result)}"
        )

    async def getblockheader(self, hash: str, verbose: bool = True) -> dict[str, Any]:
        """
        Get info block header info from the Bitcoin Core node.

        :param hash: The hash of the block header to retrieve
        :type hash: str
        :param verbose: Whether to return a verbose block header (default: True)
        :type verbose: bool
        :return: The block header information
        :rtype: dict[str, Any]

        Return Example Real Data:
                {
                    "hash": "00000000000000000000e19ae97655f89c430a301d6aa66bf6ab000bd2682524",
                    "confirmations": 29,
                    "height": 936421,
                    "version": 536903680,
                    "versionHex": "20008000",
                    "merkleroot": "1c9626b03ff111682c75a88db62b436f0d7431e620bb08d7213816a4d62b9493",
                    "time": 1771009676,
                    "mediantime": 1771008595,
                    "nonce": 1236749238,
                    "bits": "17023c7e",
                    "target": "000000000000000000023c7e0000000000000000000000000000000000000000",
                    "difficulty": 125864590119494.3,
                    "chainwork": "00000000000000000000000000000000000000010ef055be496a8b1f9a962eb4",
                    "nTx": 3160,
                    "previousblockhash": "000000000000000000012b88e14747c72b54afa7ba43874770c426fea98d2589",
                    "nextblockhash": "000000000000000000001a8c388b54f78f7c8ba95ced9fd2b517c9703e8cc91b"
                }

                or

                0080002089258da9fe26c470478743baa7af542bc74747e1882b0100000000000000000093942bd6a4163821d708bb20e631740d6f432bb68da8752c6811f13fb026961c8c768f697e3c0217b64bb749

        """

        return await self._handle_request("getblockheader", hash, verbose)

    async def getblockchaininfo(self) -> dict[str, Any]:
        """
        Get info about the blockchain from the Bitcoin Core node.

        Command:
            bitcoin-cli getblockchaininfo

        :return: The blockchain information
        :rtype: dict[str, Any]

        Return Example Real Data:
                    {
                        "chain": "main",
                        "blocks": 936451,
                        "headers": 936451,
                        "bestblockhash": "000000000000000000023577445bc9d681c4aa2935e66872687fd5273df8477a",
                        "bits": "17023c7e",
                        "target": "000000000000000000023c7e0000000000000000000000000000000000000000",
                        "difficulty": 125864590119494.3,
                        "time": 1771024690,
                        "mediantime": 1771022195,
                        "verificationprogress": 1,
                        "initialblockdownload": false,
                        "chainwork": "00000000000000000000000000000000000000010efdbffdb52e1b1f366bcc98",
                        "size_on_disk": 1951247175,
                        "pruned": true,
                        "pruneheight": 935502,
                        "automatic_pruning": true,
                        "prune_target_size": 1999634432,
                        "warnings": []
                    }

        """

        return await self._handle_request("getblockchaininfo")

    async def getblockhash(self, height: int) -> dict[str, Any]:
        """
        Get info about the blockchain from the Bitcoin Core node.

        Command:
            bitcoin-cli getblockhash <height>

        :return: The blockchain information
        :rtype: dict[str, Any]

        Return Example Real Data:
            00000000000000000000e19ae97655f89c430a301d6aa66bf6ab000bd2682524
        """

        return await self._handle_request("getblockhash", height)
