import asyncio
import math

from bitcoin_core import BitcoinCoreClient


async def check_simple() -> None:
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

            # Get recent blocks
            for i in range(bloco_count, bloco_count - 5, -1):
                block_hash = await client.getblockhash(i)
                block_info = await client.getblock(block_hash)  # type: ignore

                print(
                    f"Block {i}: Hash: {block_hash}, Transactions: {len(block_info['tx'])}, Size: {block_info['size']} bytes, Timestamp: {block_info['time']}"
                )
                # print(block_info)

        except Exception as e:
            print(f"Error fetching block template: {e}")


async def other_exemplo() -> None:

    current_height = 0
    coroutine_list = []

    (
        mining_info,
        difficulty,
        blockchain_info,
        hash_rate_10,
        hash_rate_120,
        hash_rate_2016,
    ) = None, None, None, None, None, None

    async with BitcoinCoreClient() as client:
        print("=" * 60)
        print("         BITCOIN CORE RPC - INFO MINER")
        print("=" * 60)

        try:
            coroutine_list = [
                client.getmininginfo(),
                client.getdifficulty(),
                client.getblockchaininfo(),
                client.getnetworkhashps(10),
                client.getnetworkhashps(120),
                client.getnetworkhashps(2016),
            ]
            results = await asyncio.gather(*coroutine_list)
            (
                mining_info,
                difficulty,
                blockchain_info,
                hash_rate_10,
                hash_rate_120,
                hash_rate_2016,
            ) = results

        except Exception as e:
            print(f"Error Client RPC: {e}")

        if mining_info is not None and isinstance(mining_info, dict):
            print("\n")
            print("-" * 60)
            print(">> Info Mining:")
            print("-" * 60)
            print(f"Blocks: {mining_info.get('blocks', 'N/A'):,}")
            print(f"Difficulty: {mining_info.get('difficulty', 'N/A')}")
            print(f"Network Hashrate: {mining_info.get('networkhashps', 0):,.0f} H/s")
            print(f"Pending transactions: {mining_info.get('pooledtx', 0):,}")
            print(f"Network: {mining_info.get('chain', 'N/A')}")

        if hash_rate_10 is not None and isinstance(hash_rate_10, (int, float)):
            print("\n")
            print("-" * 60)
            print(">> Hashrate 10 Blocks:")
            print("-" * 60)
            print(f"Hashrate: {hash_rate_10:,.0f} H/s")
            hours = (10 * 10) / 60
            print(f"Estimated time to find a block: {hours:.2f} hours")
            th_per_second = hash_rate_10 / 1e12  # 10^12 H/s = 1 TH/s
            print(f"Hashrate in TH/s: {th_per_second:.2f} TH/s")

        if hash_rate_120 is not None and isinstance(hash_rate_120, (int, float)):
            print("\n")
            print("-" * 60)
            print(">> Hashrate 10 Blocks:")
            print("-" * 60)
            print(f"Hashrate: {hash_rate_120:,.0f} H/s")
            hours = (120 * 10) / 60
            print(f"Estimated time to find a block: {hours:.2f} hours")
            th_per_second = hash_rate_120 / 1e12  # 10^12 H/s = 1 TH/s
            print(f"Hashrate in TH/s: {th_per_second:.2f} TH/s")

        if hash_rate_2016 is not None and isinstance(hash_rate_2016, (int, float)):
            print("\n")
            print("-" * 60)
            print(">> Hashrate 2016 Blocks:")
            print("-" * 60)
            print(f"Hashrate: {hash_rate_2016:,.0f} H/s")
            hours = (2016 * 10) / 60
            print(f"Estimated time to find a block: {hours:.2f} hours")
            th_per_second = hash_rate_2016 / 1e12  # 10^12 H/s = 1 TH/s
            print(f"Hashrate in TH/s: {th_per_second:.2f} TH/s")

        if difficulty is not None and isinstance(difficulty, (int, float)):
            print("\n")
            print("-" * 60)
            print(">> Difficulty Current:")
            print("-" * 60)
            print(f"Difficulty: {difficulty:,.2f}")

            max_taget = 0xFFFF * 256 ** (0x1D - 3)
            current_taget = max_taget / difficulty
            print(f"Current Target: {current_taget}")

            zero_aprox = int(math.log2(difficulty) / 4)  # type: ignore
            print(f"Zeros aprox: {zero_aprox}")

        if blockchain_info is not None and isinstance(blockchain_info, dict):
            print("\n")
            print("-" * 60)
            print(">> Info Last Blockchain:")
            print("-" * 60)
            current_height = blockchain_info.get("blocks", 0)
            print(f"Current Height: {current_height:,}")

            # Get Data Last Block
            block_hash = await client.getblockhash(current_height)
            block = await client.getblock(block_hash)  # type: ignore

            if block is not None and isinstance(block, dict):
                print(f"Last Block Hash: {block.get('hash', 'N/A')}")
                print(f"Last Block Time: {block.get('time', 'N/A')}")
                print(f"Last Block Tx Count: {len(block.get('tx', [])):,}")
                print(f"Last Block Size: {block.get('size', 0):,} bytes")
                print(f"Last Block Difficulty: {block.get('difficulty', 'N/A')}")
                print(f"Last Block Nonce: {block.get('nonce', 'N/A')}")

            print("\n")
            print("-" * 60)
            print(">> Time between last 5 Blocks:")
            print("-" * 60)

            header = await client.getblockheader(hash=block_hash)  # type: ignore
            block_time = header.get("time", 0)
            prev_time = block_time

            for i in range(1, 6):
                try:
                    height = current_height - i
                    block_hash = await client.getblockhash(height=height)
                    block = await client.getblock(hash=block_hash)  # type: ignore
                    header = await client.getblockheader(hash=block_hash)  # type: ignore

                    if header is not None and isinstance(header, dict):
                        block_time = header.get("time", 0)

                        diff_seconds = block_time - prev_time
                        diff_minutes = diff_seconds / 60

                        print(
                            f"Time between block {height} and {height + 1}: {diff_seconds} seconds ({diff_minutes:.2f} minutes)"
                        )

                    prev_time = block_time
                except Exception:
                    print(f"Could not retrieve block {height - i}")


if __name__ == "__main__":
    """
    Example use of the BitcoinCoreClient to fetch mining info and block templates. You can run this script to see how to interact with the Bitcoin Core node and retrieve various pieces of information about the blockchain and mining status.
    """
    asyncio.run(check_simple())
    print("\n\n")
    asyncio.run(other_exemplo())
