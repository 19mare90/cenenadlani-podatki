# Ročni pregled katalogov SPAR

```bash
python -m pip install -r requirements-spar.txt
python scripts/import_spar_pdf.py katalog.pdf
python -m unittest discover -s tests -v
```

Uvoz zapiše besedilo vseh strani in kontrolno vsoto PDF-ja v
`data/spar_prices.json`. Pri straneh brez besedila je potreben vizualni pregled.
Tudi pri straneh z besedilom je treba v PDF-ju preveriti, kateri ceni pripada
izdelek, in potrditi količino, obdobje, regijo ter pogoje kartice.

Po ročnem preverjanju vnesi ponudbo v `data/reviewed_offers.json` s povezavo na
uradni vir, datumom preverjanja `checkedAt`, veljavnostjo `validUntil`,
po možnosti `validFrom`, ter poljema `reviewStatus: approved` in `reviewedBy`.
Za lokalni preizkus vira za Android zaženi `python scripts/build_prices.py`.
Objavni workflow izdela svoj `prices.json` iz pregledanih ponudb.
