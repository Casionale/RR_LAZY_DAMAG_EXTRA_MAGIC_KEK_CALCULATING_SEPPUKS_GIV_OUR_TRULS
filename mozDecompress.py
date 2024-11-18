def mozlz4_to_text(filepath):
    # Given the path to a "mozlz4", "jsonlz4", "baklz4" etc. file, 
    # return the uncompressed text.

    try:
        import lz4.block as lz4
    except:
        import lz4

    bytestream = open(filepath, "rb")
    bytestream.read(8)  # skip past the b"mozLz40\0" header
    valid_bytes = bytestream.read()
    text = lz4.decompress(valid_bytes)
    return text