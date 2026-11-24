"""Plain-Hindi advice shown to the family. Fixed texts, so the app never words a diagnosis."""

from modules.screening.checkCatalog import Colour, Domain

DOMAIN_NAMES_HI: dict[Domain, str] = {
    "defects": "जन्म से जुड़ी समस्याएँ",
    "deficiencies": "पोषण और ख़ून की कमी",
    "diseases": "बीमारियाँ",
    "development": "विकास: बोलना, चलना, सीखना",
}

ADVICE_HI: dict[Colour, str] = {
    "green": "इस हिस्से में सब ठीक लग रहा है। बच्चे को अच्छा खाना, खेल और प्यार भरा माहौल देते रहें।",
    "yellow": (
        "इस हिस्से पर नज़र रखनी है। हम आपको WhatsApp पर रोज़ एक छोटा खेल या सलाह भेजेंगे। "
        "दो हफ़्ते में सुधार न दिखे तो आशा दीदी दोबारा जाँच करेंगी।"
    ),
    "red": (
        "इस हिस्से के लिए बच्चे को डॉक्टर को दिखाना ज़रूरी है। यह कोई पक्की बीमारी नहीं बताता, "
        "बस डॉक्टर की जाँच ज़रूरी है। रेफ़रल पर्ची पर अस्पताल का नाम और पता लिखा है।"
    ),
}

NEXT_STEP_HI = {
    "referral": "बच्चे को जल्द से जल्द रेफ़रल पर्ची में लिखे अस्पताल ले जाएँ।",
    "homePlan": "रोज़ के खेल और सलाह WhatsApp पर आएँगे। उन्हें बच्चे के साथ ज़रूर करें।",
    "none": "अगली नियमित जाँच तक बच्चे का ध्यान रखें।",
}
