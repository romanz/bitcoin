#!/usr/bin/env python3
# Copyright (c) 2019-2020 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Test the getblocklocations rpc call."""
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import (assert_equal, assert_raises_rpc_error)
from test_framework.messages import ser_vector

import pathlib


class GetblocklocationsTest(BitcoinTestFramework):
    def set_test_params(self):
        self.setup_clean_chain = True
        self.num_nodes = 1

    def run_test(self):
        """Test a trivial usage of the getblocklocations RPC command."""
        node = self.nodes[0]
        mocktime = node.getblockheader(node.getblockhash(0))['time'] + 1
        node.setmocktime(mocktime)
        self.generate(node, 7, sync_fun=self.no_op)

        NULL_HASH = '0000000000000000000000000000000000000000000000000000000000000000'
        EXPECTED_LOCATIONS = [
            {'file': 0, 'data': 8},  # genesis block
            {'file': 0, 'data': 301},
            {'file': 0, 'data': 561},
            {'file': 0, 'data': 821},
            {'file': 0, 'data': 1081},
            {'file': 0, 'data': 1341},
            {'file': 0, 'data': 1601},
            {'file': 0, 'data': 1861},
        ]

        block_hashes = [node.getblockhash(height) for height in range(len(EXPECTED_LOCATIONS))]

        # Get blocks' locations using several batch sizes
        for batch_size in range(1, 10):
            locations = node.getblocklocations(block_hashes[:batch_size])
            assert_equal(locations, EXPECTED_LOCATIONS[:batch_size])

        # Read blocks' data from the file system
        blocks_dir = pathlib.Path(node.datadir) / node.chain / 'blocks'
        with (blocks_dir / 'blk00000.dat').open('rb') as blkfile:
            for block_hash, location in zip(block_hashes, EXPECTED_LOCATIONS):
                block_bytes = bytes.fromhex(node.getblock(block_hash, 0))
                assert_file_contains(blkfile, location['data'], block_bytes)


        # Fail getting unknown block
        unknown_block_hash = '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef'
        assert_raises_rpc_error(-5, 'Block not found', node.getblocklocations, [unknown_block_hash])

        # Fail in pruned mode
        self.restart_node(0, ['-prune=1'])
        tip = block_hashes[-1]
        assert_raises_rpc_error(-1, 'Block locations are not available in prune mode', node.getblocklocations, [tip])


def assert_file_contains(fileobj, offset, data):
    fileobj.seek(offset)
    assert_equal(fileobj.read(len(data)), data)

if __name__ == '__main__':
    GetblocklocationsTest().main()
