from typing import List, Dict
from .definitions import ToolOutput, SchemeLookupInput

# Mock Database (all user-facing text in Telugu)
SCHEMES_DB = {
    "rythu_bandhu": {
        "name": "రైతు బంధు",
        "description": "వ్యవసాయ మరియు తోట పంటల పెట్టుబడి సహాయం కోసం ప్రభుత్వం ఇస్తున్న పథకం.",
        "benefits": "ప్రతి సీజన్‌కు ఒక ఎకరానికి ₹5000 సహాయం.",
        "eligibility_rules": "వ్యవసాయ భూమి ఉన్న పట్టాదారు రైతు కావాలి. గరిష్ట ఎకరాల పరిమితి లేదు.",
        "docs": ["పట్టాదారు పాస్‌బుక్", "ఆధార్ కార్డు", "బ్యాంక్ ఖాతా పాస్‌బుక్"]
    },
    "aasara_pension": {
        "name": "ఆసరా పెన్షన్",
        "description": "వృద్ధులు, విధవలు, వికలాంగుల కోసం నెలవారీ పెన్షన్ పథకం.",
        "benefits": "నెలకు సుమారు ₹2016 నుండి ₹3016 వరకు పెన్షన్.",
        "eligibility_rules": "వృద్ధాప్య పెన్షన్ కోసం వయస్సు 57 ఏళ్లు లేదా అంతకంటే ఎక్కువ ఉండాలి. గ్రామీణ ప్రాంతంలో కుటుంబ ఆదాయం 1.5 లక్షలకు లోపుగా, పట్టణంలో 2 లక్షలకు లోపుగా ఉండాలి.",
        "docs": ["ఆధార్ కార్డు", "ఫుడ్ సెక్యూరిటీ కార్డు", "బ్యాంక్ లేదా పోస్టాఫీస్ ఖాతా వివరాలు"]
    },
    "kalyana_lakshmi": {
        "name": "కళ్యాణ లక్ష్మి",
        "description": "ఎస్సీ/ఎస్టీ/బీసీ/అల్పసంఖ్యాకుల వర్గాల పేద బాలికల వివాహం కోసం ఆర్థిక సహాయం.",
        "benefits": "ఒకేసారి సుమారు ₹1,00,116 ఆర్థిక సహాయం.",
        "eligibility_rules": "వధువు వయస్సు కనీసం 18 సంవత్సరాలు ఉండాలి. తల్లిదండ్రుల వార్షిక ఆదాయం 2 లక్షలకు లోపుగా ఉండాలి.",
        "docs": ["వివాహ ధృవీకరణ పత్రం", "ఆదాయ ధృవీకరణ పత్రం", "కుల ధృవీకరణ పత్రం", "ఆధార్ కార్డు"]
    }
}

class SchemeKnowledgeRetriever:
    def search(self, args: SchemeLookupInput) -> ToolOutput:
        """
        Searches for schemes based on ID or keywords.
        """
        # Direct ID Lookup
        if args.scheme_id:
            scheme = SCHEMES_DB.get(args.scheme_id.lower())
            if scheme:
                return ToolOutput(success=True, data=scheme)
            
            # Fuzzy / Spelling check could go here
            return ToolOutput(
                success=False,
                error="ఆ పథకం ఐడీ లభించలేదు. దయచేసి పేరు లేదా వివరాలు మళ్లీ చెప్పండి."
            )

        # Keyword Search
        keywords = args.keywords_list
        if keywords:
            results = []
            for sid, data in SCHEMES_DB.items():
                # Simple containment check
                text_blob = (data['name'] + " " + data['description']).lower()
                if any(k.lower() in text_blob for k in keywords):
                    results.append(data)
            
            if results:
                return ToolOutput(success=True, data={"matches": results})
            return ToolOutput(
                success=False,
                error="మీరు చెప్పిన వివరాలకు సరిపోయే పథకాలు కనబడలేదు."
            )

        return ToolOutput(
            success=False,
            error="సర్చ్ చేయడానికి అవసరమైన వివరాలు ఇవ్వలేదు."
        )
