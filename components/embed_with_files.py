from discord import Embed, File


class EmbedWithFiles:
    def __init__(self, embed: Embed, files: list[str]):
        self.embed: embed = embed
        self.files: list[File] = []
        for filepath in files:
            self.files.append(File(filepath))