#!/usr/bin/env python3
"""
Python re-implementation of the COBOL program in cobol/src/program.cbl.
Run from the cobol/ directory so that relative paths match.
"""

import os

def read_fixed_records(path, rec_len):
    """Read a fixed-length sequential file (no delimiters)."""
    if not os.path.exists(path):
        return []
    with open(path, "rb") as f:
        data = f.read()
    records = []
    for i in range(0, len(data), rec_len):
        chunk = data[i:i + rec_len]
        if len(chunk) < rec_len:
            chunk = chunk + b" " * (rec_len - len(chunk))
        records.append(chunk)
    return records

def write_fixed_records(path, records, rec_len):
    """Write fixed-length records back to the file."""
    with open(path, "wb") as f:
        for rec in records:
            if len(rec) < rec_len:
                rec = rec + b" " * (rec_len - len(rec))
            elif len(rec) > rec_len:
                rec = rec[:rec_len]
            f.write(rec)

def main():
    # Record lengths matching the COBOL FD definitions
    ACC_LEN = 4 + 20 + 10  # 34
    BOOK_LEN = 4 + 20 + 4  # 28
    TRANS_LEN = 4 + 10 + 4 + 4  # 22
    INPUT_LEN = 4 + 4 + 4 + 10  # 22

    input_path = "src/INPUT.DAT"
    accounts_path = "data/ACCOUNTS.DAT"
    books_path = "data/BOOKS.DAT"
    trans_path = "data/TRANSACTIONS.DAT"

    # Read input
    input_recs = read_fixed_records(input_path, INPUT_LEN)
    if not input_recs:
        print("Error: Input file is empty")
        return

    inp = input_recs[0]
    ws_buyer_id = inp[0:4].decode("ascii", errors="ignore").rstrip()
    ws_seller_id = inp[4:8].decode("ascii", errors="ignore").rstrip()
    ws_book_id = inp[8:12].decode("ascii", errors="ignore").rstrip()
    amount_raw = inp[12:22].decode("ascii", errors="ignore").strip()
    try:
        ws_amount = int(amount_raw) if amount_raw else 0
    except ValueError:
        ws_amount = 0

    # Validate users and book
    ws_buyer_found = False
    ws_seller_found = False
    ws_book_found = False
    ws_valid_owner = False

    # Check accounts
    accounts = read_fixed_records(accounts_path, ACC_LEN)
    for rec in accounts:
        acc_id = rec[0:4].decode("ascii", errors="ignore")
        if acc_id == ws_buyer_id:
            ws_buyer_found = True
        if acc_id == ws_seller_id:
            ws_seller_found = True

    # Check books
    books = read_fixed_records(books_path, BOOK_LEN)
    for rec in books:
        book_id = rec[0:4].decode("ascii", errors="ignore")
        if book_id == ws_book_id:
            ws_book_found = True
            owner = rec[24:28].decode("ascii", errors="ignore")
            if owner == ws_seller_id:
                ws_valid_owner = True

    print(" ")  # matching the DISPLAY " " in VALIDATE

    if not (ws_buyer_found and ws_seller_found and ws_book_found and ws_valid_owner):
        print("Transaction failed due to validation errors")
        return

    # Process transaction
    # Update accounts
    for i, rec in enumerate(accounts):
        acc_id = rec[0:4].decode("ascii", errors="ignore")
        name = rec[4:24]
        bal_str = rec[24:34].decode("ascii", errors="ignore").strip()
        try:
            balance = int(bal_str) if bal_str else 0
        except ValueError:
            balance = 0
        if acc_id == ws_buyer_id:
            balance -= ws_amount
        if acc_id == ws_seller_id:
            balance += ws_amount
        # Format balance as 10 zero-padded digits (COBOL PIC 9(10))
        new_bal = f"{max(0, balance):010d}".encode("ascii")  # prevent negative if any
        accounts[i] = rec[0:24] + new_bal

    write_fixed_records(accounts_path, accounts, ACC_LEN)

    # Update books: change owner to buyer
    for i, rec in enumerate(books):
        book_id = rec[0:4].decode("ascii", errors="ignore")
        if book_id == ws_book_id:
            books[i] = rec[0:24] + ws_buyer_id.encode("ascii").ljust(4)

    write_fixed_records(books_path, books, BOOK_LEN)

    # Append transaction
    trans_rec = (
        ws_book_id.encode("ascii").ljust(4) +
        f"{ws_amount:010d}".encode("ascii") +
        ws_seller_id.encode("ascii").ljust(4) +
        ws_buyer_id.encode("ascii").ljust(4)
    )
    with open(trans_path, "ab") as f:
        f.write(trans_rec)

    print("Transaction completed successfully")

if __name__ == "__main__":
    main()
