#!/usr/bin/env python3

"""
BitcoinRPCClient is an asynchronous client for communicating with a lib BitcoinRPC.
"""

import asyncio
from typing import Any, Literal, Optional

import httpx
from bitcoinrpc import BitcoinRPC  # type: ignore
from dotenv import dotenv_values

config = dotenv_values("env/BitcoinRPC.env")


class BitcoinRPCClient:
    """
    Client async to comunication with BitcoinRPC.

    Implementation the pattern Wrapper on the BitcoinRPC library with manager automatic concection through context manager.

    Use:
        async with BitcoinRPCClient(...) as client:
            block = await client.get_block_by_hash(block_hash)
    """

    def __init__(
        self,
        rcp_user: Optional[str] = None,
        rcp_password: Optional[str] = None,
        rcp_host: Optional[str] = None,
        rcp_port: Optional[str] = None,
    ) -> None:
        """
        Initialize the BitcoinRPCClient with credenciais RPC.

        :param rcp_user: Username for RPC authentication
        :type rcp_user: Optional[str]
        :param rcp_password: Password for RPC authentication
        :type rcp_password: Optional[str]
        :param rcp_host: Host address for RPC connection
        :type rcp_host: Optional[str]
        :param rcp_port: Port for RPC connection
        :type rcp_port: Optional[str]
        """
        self._host = rcp_host or config["RPC_HOST"]
        self._port = rcp_port or config["RPC_PORT"]
        self._username = rcp_user or config["RPC_USER"]
        self._password = rcp_password or config["RPC_PASSWORD"]
        self._url = f"http://{self._host}:{self._port}"

        # Conection will start in __aenter__ and close in __aexit__
        self._btc_con: Optional[BitcoinRPC] = None
        self._http_client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "BitcoinRPCClient":
        """Connect to the Bitcoin RPC server when entering the context."""

        # Create the client AsyncClient for HTTP requests
        auth_value = (
            (self._username, self._password)
            if self._username is not None and self._password is not None
            else None
        )
        self._http_client = httpx.AsyncClient(
            auth=auth_value,
            timeout=10.0,
        )

        # Create the connection BitcoinRPC using the httpx client
        self._btc_con = BitcoinRPC(
            self._url,
            client=self._http_client,
        )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close the connection to the Bitcoin RPC server when exiting the context."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

        self._btc_con = None

    # Methods Auxiliares
    def _ensure_connection(self) -> BitcoinRPC:
        if not self._btc_con:
            raise RuntimeError(
                "BitcoinRPC client is not connected. Use 'async with BitcoinRPCClient(...) as client' to establish a connection."
            )
        return self._btc_con

    async def acall_rpc(self, method: str, *args) -> Any:
        """
        Call a generic RPC method with the provided arguments.

        :param method: The name of the RPC method to call
        :type method: str
        :param args: Arguments to pass to the RPC method
        :type args: Any
        """
        conn = self._ensure_connection()
        try:
            return await conn.acall(method, *args)
        except Exception as e:
            raise RuntimeError(f"Error calling RPC method '{method}': {e}")

    # Methods to interact with the Bitcoin network RPC

    async def getmininginfo(self) -> dict[str, Any]:
        """
        Returns a json object containing mining-related information.

        Result example:
            {
                'blocks': 935956,
                'bits': '17023c7e',
                'difficulty': 125864590119494.3,
                'target': '000000000000000000023c7e0000000000000000000000000000000000000000',
                'networkhashps': 9.124053172201868e+20,
                'pooledtx': 6715,
                'blockmintxfee': 1e-08,
                'chain': 'main',
                'next': {
                            'height': 935957,
                            'bits': '17023c7e',
                            'difficulty': 125864590119494.3,
                            'target': '000000000000000000023c7e0000000000000000000000000000000000000000'
                        },
                'warnings': []
            }
        """

        conn = self._ensure_connection()
        try:
            return await conn.getmininginfo()  # type: ignore
        except Exception as e:
            raise RuntimeError(f"Error calling RPC method 'getmininginfo': {e}")

    async def getblockchaininfo(self) -> dict[str, Any]:
        """
        Returns an object containing various state info regarding blockchain processing.

        Result example:
            {
                'chain': 'main',
                'blocks': 935960,
                'headers': 935960,
                'bestblockhash': '000000000000000000003ec3d1f7d949339df57b7d17c6dc4149246d42ba13bc',
                'bits': '17023c7e', 'target': '000000000000000000023c7e0000000000000000000000000000000000000000',
                'difficulty': 125864590119494.3,
                'time': 1770762065,
                'mediantime': 1770758535,
                'verificationprogress': 1,
                'initialblockdownload': False,
                'chainwork': '00000000000000000000000000000000000000010e2230cd95b5eee15987df1e',
                'size_on_disk': 1956098917,
                'pruned': True,
                'pruneheight': 935011,
                'automatic_pruning': True,
                'prune_target_size': 1999634432,
                'warnings': []
            }
        """

        conn = self._ensure_connection()
        try:
            return await conn.getblockchaininfo()  # type: ignore
        except Exception as e:
            raise RuntimeError(f"Error calling RPC method 'getblockchaininfo': {e}")

    async def getbestblockhash(self) -> str:
        """
        Returns the hash of the best (tip) block in the most-work fully-validated chain.
        Result example:
            '00000000000000000001dc83907b6c66df6518879c83cec53b86d5b306df4786'
        """

        conn = self._ensure_connection()
        try:
            # Example: await conn.acall("getbestblockhash", [])
            # return await conn.getbestblockhash()
            return await conn.acall("getbestblockhash", [])

        except Exception as e:
            raise RuntimeError(f"Error calling RPC method 'getbestblockhash': {e}")

    async def getdifficulty(self) -> float:
        """
        Returns the proof-of-work difficulty as a multiple of the minimum difficulty.


        Result example:
            123543.15654
            type: float
        """

        conn = self._ensure_connection()
        try:
            return await conn.getdifficulty()

        except Exception as e:
            raise RuntimeError(f"Error calling RPC method 'getdifficulty': {e}")

    async def getblock(self, blockhash: str, verbosity: Literal[0, 1, 2] = 1) -> Any:
        """
        Return info for a block.

        :param blockhash: The block hash
        :type blockhash: str
        :param verbosity: 0 for hex-encoded block data, 1 for a json object, and 2 for json object with transaction data
        :type verbosity: int
        :return: Block information
        :rtype: Any
        """

        conn = self._ensure_connection()
        try:
            return await conn.getblock(blockhash, verbosity)

        except Exception as e:
            raise RuntimeError(f"Error calling RPC method 'getblock': {e}")

    # Methods Property
    @property
    def is_connected(self) -> bool:
        """Check if the client is connected to the Bitcoin RPC server."""
        return self._btc_con is not None

    @property
    def url(self) -> str:
        """Get the URL (Just read) of the Bitcoin RPC server."""
        return self._url


async def main():
    async with BitcoinRPCClient() as client:
        # mining_info = await client.getblock(
        #     "0000000000000000000181222b70dee865fe59a572fc7bb2038f077cd293fd77"
        # )

        mining_info = await client.getmininginfo()
        print(mining_info)

        print(client.is_connected)
        print(client.url)


if __name__ == "__main__":
    asyncio.run(main())
