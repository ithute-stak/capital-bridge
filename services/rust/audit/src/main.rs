use sha2::{Digest, Sha256};
use std::io::{self, Read};

fn digest(payload: &[u8]) -> String {
    format!("{:x}", Sha256::digest(payload))
}
fn main() {
    let mut input = Vec::new();
    io::stdin().read_to_end(&mut input).expect("read audit bytes");
    println!("{}", digest(&input));
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn deterministic_digest() {
        assert_eq!(digest(b"abc"), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
    }
}
