from database.core_s3 import s3_client
import asyncio
import sys


if __name__ == "__main__":
    if "--create-bucket" in sys.argv:
        asyncio.run(s3_client.create_bucket())
