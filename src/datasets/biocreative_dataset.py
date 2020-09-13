from torch.utils.data import Dataset


class BiocreativeDataset(Dataset):
    """
    Represents a biocreative II dataset
    """

    def __init__(self, train_file_or_handle, annotation_file_or_handle, transformer=None):
        # Load raw train
        self.transformer = transformer
        self._text_lines = self._parse(self._readlines(train_file_or_handle))

        # Load annotations
        self._annotation = self._parse_annotation(self._readlines(annotation_file_or_handle))

    def _readlines(self, file_or_handle):
        if isinstance(file_or_handle, str):
            with open(file_or_handle, "r") as f:
                lines = f.readlines()
        else:
            lines = file_or_handle.readlines()

        return lines

    def __len__(self):
        return len(self._text_lines)

    def __getitem__(self, item):
        id, text = self._text_lines[item]["id"], self._text_lines[item]["text"]
        annotations = self._annotation.get(id, None)

        token_text, token_labels = self._tokenise(text, annotations)

        return token_text, token_labels

    def _parse(self, raw_lines):
        result = []
        for r in raw_lines:
            id, text = r.split(" ")[0], " ".join(r.split(" ")[1:])

            result.append({
                "id": id,
                "text": text.rstrip("\n")
            })
        return result

    def _parse_annotation(self, annotation_lines):
        result = {}
        for l in annotation_lines:
            id, pos_tuple, text = l.split("|")
            text = text.rstrip("\n")

            start, end = pos_tuple.split(" ")

            if id not in result:
                result[id] = []

            result[id].append({
                # Convert to zero indexed
                "start": int(start) - 1
                , "end": int(end) - 1
                , "text": text
            })
        return result

    def _tokenise(self, line, annotation=None):
        if annotation is None:
            return [line], ["o"]

        tokens = []
        tokens_labels = []

        sorted_annotations = sorted(annotation, key=lambda item: item["start"])

        i = 0
        for item in sorted_annotations:
            # Find true position within approximate locations specified
            token_span = line[item["start"]:item["end"] + len(item["text"])]
            span_index = token_span.find(item["text"])
            length = len(item["text"])

            assert span_index > -1, "Could not find {} in span {}".format(item["text"], token_span, )

            start_pos = item["start"] + span_index

            # If other token
            other_token = line[i: start_pos]
            if len(other_token) > 0:
                tokens.append(other_token)
                tokens_labels.append("o")

            # Start entity
            end_pos = start_pos + length
            entity_token = line[start_pos: end_pos]
            tokens.append(entity_token)
            tokens_labels.append("s")

            i=end_pos

        other_token = line[i:]
        if len(other_token) > 0:
            tokens.append(other_token)
            tokens_labels.append("o")

        return tokens, tokens_labels
