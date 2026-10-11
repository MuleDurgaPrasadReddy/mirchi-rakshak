from typing import Dict, Any


class TranslationService:
    def get_localized_unmatched_response(self, is_person: bool, is_mango: bool, language: str = "en") -> Dict[str, str]:
        """
        Returns localized diagnostic error messages for non-chili or human photos.
        """
        lang = language.lower()
        if is_mango:
            if lang == "te":
                return {
                    "disease": "అప్‌లోడ్ చేసిన ఫోటో మామిడి ఆకు - మిరప ఆకుతో పోలలేదు",
                    "invalid_reason": "ఈ ఫోటో మామిడి ఆకు (Mango leaf). ఇది మిరప ఆకుతో పోలడం లేదు. దయచేసి మిరప ఆకును మాత్రమే స్కాన్ చేయండి.",
                }
            elif lang == "hi":
                return {
                    "disease": "अपलोड की गई फोटो आम के पत्ते की है और मिर्च के पत्ते से मेल नहीं खाती",
                    "invalid_reason": "यह फोटो आम के पत्ते की है। यह मिर्च के पत्ते से मेल नहीं खाती। कृपया मिर्च के पौधे की फोटो लें।",
                }
            else:
                return {
                    "disease": "The uploaded image is a Mango leaf and does not match a chili leaf",
                    "invalid_reason": "The scanned image is a Mango leaf and does not match a chili crop leaf profile. Please scan or upload a clear photo of a chili plant leaf or pod.",
                }
        elif is_person:
            if lang == "te":
                return {
                    "disease": "అప్‌లోడ్ చేసిన ఫోటో మనిషిది - మిరప ఆకుతో పోలలేదు",
                    "invalid_reason": "ఈ ఫోటోలో మనిషి ఉన్నారు. ఇది మిరప ఆకు లేదా మొక్క ఫొటోతో పోలడం లేదు. దయచేసి మిరప ఆకును మాత్రమే స్కాన్ చేయండి.",
                }
            elif lang == "hi":
                return {
                    "disease": "अपलोड की गई फोटो एक व्यक्ति की है और मिर्च के पत्ते से मेल नहीं खाती",
                    "invalid_reason": "इस फोटो में व्यक्ति दिखाई दे रहा है। यह मिर्च के पत्ते की फोटो से मेल नहीं खाती। कृपया मिर्च के पत्ते की फोटो लें।",
                }
            else:
                return {
                    "disease": "The uploaded image is a human photo and does not match a chili leaf",
                    "invalid_reason": "This image contains a person and does not match a chili leaf image. Please capture a clear photo of a chili leaf or plant.",
                }
        else:
            if lang == "te":
                return {
                    "disease": "అప్‌లోడ్ చేసిన ఫోటో మిరప ఆకు కాదు (Image does not match chili leaf)",
                    "invalid_reason": "అప్‌లోడ్ చేసిన ఫోటో మిరప ఆకుతో పోలలేదు. దయచేసి మిరప ఆకు లేదా కాయ ఫోటోను మాత్రమే స్కాన్ చేయండి.",
                }
            elif lang == "hi":
                return {
                    "disease": "अपलोड की गई फोटो मिर्च का पत्ता नहीं है (Image does not match chili leaf)",
                    "invalid_reason": "अपलोड की गई फोटो मिर्च के पत्ते से मेल नहीं खाती। कृपया केवल मिर्च के पौधे की फोटो लें।",
                }
            else:
                return {
                    "disease": "The uploaded image is not a chili leaf",
                    "invalid_reason": "The scanned image does not match a chili leaf. Please upload or scan a clear photo of a chili plant leaf or pod.",
                }


translation_service = TranslationService()
