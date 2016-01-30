from __future__ import absolute_import
from Crypto.PublicKey import RSA
from Crypto import Random
from Crypto.Hash import SHA256

import logging
log = logging.getLogger('offlinetools.keymgmt')


def generate_new_keypair():
    rng = Random.new().read

    key = RSA.generate(1024, rng)
    return key.exportKey(), key.publickey().exportKey()


def load_key(keytext):
    return RSA.importKey(keytext)


def get_signature(keytext, tosign):
    digest = SHA256.new(tosign).digest()
    key = load_key(keytext)
    rng = Random.new().read
    sig = key.sign(digest, rng)
    return sig


