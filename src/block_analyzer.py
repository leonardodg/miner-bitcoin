#!/usr/bin/env python3

""" "
BlockAnalyzer is a module for analyzing Bitcoin blocks and transactions.
"""

from typing import Any, List

from bitcoin_core import BitcoinCoreClient


class BlockAnalyzer:
    """
    BlockAnalyzer provides methods to analyze Bitcoin blocks and transactions, such as calculating transaction fees, identifying transaction types, and more. It can be used to gain insights into the Bitcoin blockchain and understand the behavior of transactions and blocks.
    """

    def __init__(self, rpc_client: "BitcoinCoreClient") -> None:
        """Initialize the BlockAnalyzer with a Bitcoin Core RPC client."""
        self.rpc_client = rpc_client

    async def get_block_details(self, hash: str) -> dict:
        """
        Get detailed information about a specific block by its hash.

        :param hash: The hash of the block to analyze
        :type hash: str
        :return: A dictionary containing analysis results of the block
        :rtype: dict
        """
        return await self.rpc_client.getblock(hash)

    async def get_block_template(
        self, count: int = 10, resume: bool = True
    ) -> List[dict]:
        """Get blocks template from the blockchain.

        :param count: The number of recent blocks to retrieve
        :type count: int
        :return: A list of dictionaries containing block information
        :rtype: List[dict]
        """
        blocks = []
        result = await self.rpc_client.getblocktemplate()
        for block in result["transactions"]:
            if resume:
                blocks.append(
                    {
                        "hash": block["hash"],
                        "target": block["target"],
                        "height": block["height"],
                        "difficulty": block["difficulty"],
                        "bits": block["bits"],
                        "nonce": block["nonce"],
                        "tx": block["tx"],
                        "ntx": len(block["tx"]),
                        "size": block["size"],
                        "weight": block["weight"],
                        "time": block["time"],
                    }
                )
            else:
                blocks.append(block)
        return blocks[:count]

    async def get_recent_blocks(self, count: int = 10) -> list[dict[str, Any]]:
        """
        Get recent blocks from the Bitcoin Core node.

        :param count: The number of recent blocks to retrieve
        :type count: int
        :return: A list of recent blocks
        :rtype: list[dict[str, Any]]
        """
        currenty_block = await self.rpc_client.getblockcount()
        blocks = []

        for i in range(currenty_block, currenty_block - count, -1):
            block_hash = await self.rpc_client.getblockhash(i)
            block_info = await self.rpc_client.getblock(block_hash)  # type: ignore
            # print(
            #     f"Block {i}: Hash: {block_hash}, Transactions: {len(block_info['tx'])}, Size: {block_info['size']} bytes, Timestamp: {block_info['time']}"
            # )
            blocks.append(block_info)

        return blocks

    def bits_to_target(self, bits: int) -> int:
        """
        Convert the compact representation of the target (bits) to the full target value.

        :param bits: The compact representation of the target
        :type bits: int
        :return: The full target value
        :rtype: int
        """
        exponent = bits >> 24
        mantissa = bits & 0xFFFFFF
        target = mantissa * (1 << (8 * (exponent - 3)))
        return target

    def bits_to_difficulty(self, bits: int) -> float:
        """
        Convert the compact representation of the target (bits) to the difficulty.

        :param bits: The compact representation of the target
        :type bits: int
        :return: The difficulty
        :rtype: float
        """
        target = self.bits_to_target(bits)
        difficulty = 0xFFFF * 256 ** (0x1D - 3) / target
        return difficulty

    def analyze_block_difficulty(
        self, blocks: list[dict[str, Any]]
    ) -> dict[str, float | str | tuple[float, float] | None]:
        """
        Analyze the difficulty of a list of blocks and add the difficulty information to each block.

        :param blocks: A list of blocks to analyze
        :type blocks: list[dict[str, Any]]
        :return: A list of blocks with added difficulty information
        :rtype: list[dict[str, Any]]
        """

        difficulties = []

        for block in blocks:
            bits = block.get("bits", 0)
            if bits is not None:
                difficulties.append(self.bits_to_difficulty(bits))

        return {
            "current_difficulty": difficulties[0] if difficulties else None,
            "average_difficulty": sum(difficulties) / len(difficulties)
            if difficulties
            else None,
            "min_difficulty": min(difficulties) if difficulties else None,
            "max_difficulty": max(difficulties) if difficulties else None,
            "trend": "increasing"
            if len(difficulties) > 1 and difficulties[-1] > difficulties[0]
            else "decreasing"
            if len(difficulties) > 1 and difficulties[-1] < difficulties[0]
            else "stable",
            "difficulties_range": (min(difficulties), max(difficulties))
            if difficulties
            else None,
        }

    def analyze_mining_time(
        self, blocks: list[dict[str, Any]]
    ) -> dict[str, float | str | tuple[float, float] | None]:
        """
        Analyze the mining time of a list of blocks and add the mining time information to each block.

        :param blocks: A list of blocks to analyze
        :type blocks: list[dict[str, Any]]
        :return: A list of blocks with added mining time information
        :rtype: list[dict[str, Any]]
        """

        mining_times = []

        for block in blocks:
            time = block.get("time", 0)
            if time is not None:
                mining_times.append(time)

        return {
            "average_mining_time": sum(mining_times) / len(mining_times)
            if mining_times
            else None,
            "slowest_mining_time": min(mining_times) if mining_times else None,
            "fastest_mining_time": max(mining_times) if mining_times else None,
        }
