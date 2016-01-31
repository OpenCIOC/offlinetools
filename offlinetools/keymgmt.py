# =========================================================================================
#  Copyright 2016 Community Information Online Consortium (CIOC) and KCL Software Solutions
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# =========================================================================================

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
