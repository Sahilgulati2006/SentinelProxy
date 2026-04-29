import re


class ReidentificationResult:
    def __init__(
        self,
        restored_text: str,
        reidentification_applied: bool,
        unreplaced_placeholders: list[str],
        repaired_placeholders: list[str],
    ):
        self.restored_text = restored_text
        self.reidentification_applied = reidentification_applied
        self.unreplaced_placeholders = unreplaced_placeholders
        self.repaired_placeholders = repaired_placeholders


class ReidentificationService:
    EXACT_PATTERN = re.compile(r"<<SP_[A-Z_]+_\d+>>")
    MALFORMED_PATTERN = re.compile(r"<<SP_[A-Z_]+_\d+>|SP_[A-Z_]+_\d+")

    def restore(self, text: str, mappings: dict[str, str]) -> ReidentificationResult:
        restored_text = text
        replaced_any = False
        repaired_placeholders: list[str] = []

        # 1) Exact replacement first
        for placeholder, original in sorted(mappings.items(), key=lambda x: len(x[0]), reverse=True):
            if placeholder in restored_text:
                restored_text = restored_text.replace(placeholder, original)
                replaced_any = True

        # 2) Conservative repair for near-miss variants
        for placeholder, original in sorted(mappings.items(), key=lambda x: len(x[0]), reverse=True):
            canonical = placeholder
            missing_one_bracket = placeholder[:-1]  # <<SP_EMAIL_1>
            bare = placeholder.replace("<<", "").replace(">>", "")  # SP_EMAIL_1

            for variant in [missing_one_bracket, bare]:
                if variant in restored_text:
                    restored_text = restored_text.replace(variant, original)
                    repaired_placeholders.append(variant)
                    replaced_any = True

        unreplaced = sorted(
            set(self.EXACT_PATTERN.findall(restored_text)) |
            set(self.MALFORMED_PATTERN.findall(restored_text))
        )

        return ReidentificationResult(
            restored_text=restored_text,
            reidentification_applied=replaced_any,
            unreplaced_placeholders=unreplaced,
            repaired_placeholders=sorted(set(repaired_placeholders)),
        )