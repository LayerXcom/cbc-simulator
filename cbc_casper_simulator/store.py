from __future__ import annotations
from typing import Dict, List, Optional
from cbc_casper_simulator.message import Message
from cbc_casper_simulator.block import Block
from typing import TYPE_CHECKING
from typing import Union
if TYPE_CHECKING:
    from cbc_casper_simulator.validator import Validator


class Store:
    def __init__(self):
        self.message_history: Dict[Validator, List[int]] = dict()
        self.messages: Dict[int, Message] = dict()
        self.children: Dict[int, List[int]] = dict()
        self.parent: Dict[int, int] = dict()
        self.block_to_message_in_hash: Dict[int, int] = dict()
        self.genesis: Optional[Message] = None
        self.last_finalized_block: Optional[Block] = None

    def add(self, message):
        self.block_to_message_in_hash[message.estimate.hash] = message.hash
        self.messages[message.hash] = message

        self.message_history.setdefault(message.sender, [])
        self.message_history[message.sender].append(message.hash)

        if message.is_genesis():
            self.genesis = message
        else:
            parent_message_hash = self.block_to_message_in_hash[message.estimate.parent_hash]
            self.parent[message.hash] = parent_message_hash
            self.children.setdefault(parent_message_hash, [])
            self.children[parent_message_hash].append(message.hash)

        self.last_finalized_block = message.estimate

    def message(self, hash: int) -> Optional[Message]:
        return self.messages.get(hash, None)

    def latest_message_hashes(self) -> Dict['Validator', int]:
        return {v: l[-1] for (v, l) in self.message_history.items()}

    def latest_messages(self) -> Dict['Validator', Message]:
        return {v: self.message(l[-1]) for (v, l) in self.message_history.items()}

    def parent_message(self, hash_or_message: Union[int, Message]) -> Optional[Message]:
        message = self.messages[hash_or_message] if isinstance(
            hash_or_message, int) else hash_or_message
        parent_hash = self.parent.get(message.hash, None)
        return self.messages.get(parent_hash, None)

    def children_messages(self, hash_or_message: Union[int, Message]) -> List[Message]:
        message = self.messages[hash_or_message] if isinstance(
            hash_or_message, int) else hash_or_message
        children_hash = self.children.get(message.hash, [])
        return [self.messages[child] for child in children_hash]

    def parent_block(self, hash_or_block: Union[int, Block]) -> Optional[Block]:
        block_hash = hash_or_block if isinstance(
            hash_or_block, int) else hash_or_block.hash
        message_hash = self.block_to_message_in_hash.get(block_hash, None)
        parent_message_hash = self.parent.get(message_hash, None)
        message = self.messages.get(parent_message_hash, None)
        return message.estimate if message is not None else None

    def children_blocks(self, hash_or_block: Union[int, Block]) -> List[Block]:
        block_hash = hash_or_block if isinstance(
            hash_or_block, int) else hash_or_block.hash
        message_hash = self.block_to_message_in_hash.get(block_hash, None)
        children_message_hashes = self.children.get(message_hash, [])
        return [self.messages[child].estimate for child in children_message_hashes]

    def has_children_blocks(self, hash_or_block: Union[int, Block]) -> bool:
        return len(self.children_blocks(hash_or_block)) > 0

    def to_message(self, hash_or_block: Union[int, Block]) -> Optional[Message]:
        block_hash = hash_or_block if isinstance(
            hash_or_block, int) else hash_or_block.hash
        message_hash = self.block_to_message_in_hash.get(block_hash, None)
        return self.messages.get(message_hash, None)

    def to_block(self, hash_or_message: Union[int, Message]) -> Optional[Block]:
        message = self.messages[hash_or_message] if isinstance(
            hash_or_message, int) else hash_or_message
        return message.estimate

    def justified(self, hash_or_message: Union[int, Message]) -> bool:
        message_hash = hash_or_message if isinstance(
            hash_or_message, int) else hash_or_message.hash
        return message_hash in self.messages

    def genesis_block(self) -> Block:
        return self.genesis.estimate

    def dump(self, state=None):
        return [m.dump(state, self.parent_message(m.hash)) for m in self.messages.values()]
