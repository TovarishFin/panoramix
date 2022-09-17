# Panoramix

This is an EVM decompiler.

It is a fork of a fork of the Panoramix original repo that's not maintained actively by its author/s anymore: https://github.com/palkeo/panoramix.git

The goal of this fork is to maintain Panoramix in a decent shape and to implement the missing opcode from the london hardfork, `basefee`.
A longer term goal is to add type annotations for better readability.

The code quality is still not great and the software is complex, it's mostly reserved for advanced users.

## Installation

```console
$ pip install panoramix-decompiler
```

## Running

You can specify a web3 provider using the environment variable `WEB3_PROVIDER_URI`. In this case a local provider was set.

```console
$ WEB3_PROVIDER_URI=http://localhost:7545 panoramix 0x0d94D81FD712126E7f320b5B10537D01d6a01563
```

You can also provide the bytecode for decompilation.

```console
$ panoramix 6004600d60003960046000f30011223344
```

## Examples

Here is an example contract using `basefee`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.14;

contract BaseFeeTest {
    uint256 public x;
    function setInt() external {
        if (block.basefee > 5e9) {
            x = block.basefee;
        } else {
            x = 0;
        }
    }
    function getBaseFee() external view returns (uint256) {
        return block.basefee;
    }

    function getBaseFeePlusOffset(uint256 _offset) external view returns(uint256) {
        return block.basefee + _offset;
    }
}
```

The compiled code can be decompiled using:

```sh
python main.py 0x6080604052348015600f57600080fd5b506004361060465760003560e01c80630c55699c14604b57806315e812ad1460655780633a0a75e014606a57806367bff126146079575b600080fd5b605360005481565b60405190815260200160405180910390f35b486053565b6053607536600460a9565b6081565b607f6091565b005b6000608b824860c1565b92915050565b64012a05f20048111560a35748600055565b60008055565b60006020828403121560ba57600080fd5b5035919050565b6000821982111560e157634e487b7160e01b600052601160045260246000fd5b50019056fea2646970667358221220dd449e8b428bd48df76442a228047423c6f53f313140011a8eea5d2e85b1ac6364736f6c634300080e0033
```

it output...

```python
const getBaseFee = block.basefee

def storage:
  x is uint256 at storage 0

def x() payable:
  return x

#
#  Regular functions
#

def _fallback() payable: # default function
  revert

def unknown67bff126() payable:
  if block.basefee <= 5 * 10^9:
      x = 0
  else:
      x = block.basefee

def unknown3a0a75e0(uint256 _param1) payable:
  require calldata.size - 4 >=′ 32
  if block.basefee > !_param1:
      revert with 0, 17
  return (block.basefee + _param1)
```
