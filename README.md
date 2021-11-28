# wannacry_monero_tracing
consolidation_txs.csv contains XMR TXIDs for the consolidation transactions as described in article, as well as the integer identifiers for the TXOs being spent. 

wannashift.json contains the BTC to XMR ShapeShift API data as identified by Neutrino.

xmr_to_bch_transactions.json contains the XMR to BCH ShapeShift API data.

bch_to_xmr_archives.csv contains URLs of waybackmachine snapshots of the XMR to BCH ShapeShift. Some were mistakenly not archived prior to ShapeShift plugging the leak. 

# Menelaus
*He became in turn a bearded lion, a snake, a panther, a monstrous boar; then running water, then a towering and leafy tree; but we kept our hold, unflinching and undismayed, and in the end this master of dreaded secrets began to tire.*

menelausXMR0.3.py is some PoC code I hacked together to get XMR deposits to ShapeShift.io. The method was [disclosed to ShapeShift in 2020 and fixed in 2021](https://www.bankinfosecurity.com/crypto-exchange-bug-reveals-north-korean-monero-laundering-a-17629) so it won't work anymore. Nevertheless, some of the snippets might be useful for people who want to analyze Monero using python.  
