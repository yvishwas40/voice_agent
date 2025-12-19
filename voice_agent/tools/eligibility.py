from .definitions import ToolOutput, EligibilityInput

class EligibilityEngine:
    def check(self, input_data: EligibilityInput, scheme_id: str) -> ToolOutput:
        """
        Determines eligibility for a specific scheme based on rules.
        """
        if not scheme_id:
            return ToolOutput(
                success=False,
                error="అర్హతను చెక్ చేయడానికి ముందుగా ఏ పథకం కోసం చూడాలి అనేది (స్కీమ్ ఐడీ) చెప్పాలి."
            )

        rule_method = getattr(self, f"_check_{scheme_id}", None)
        if not rule_method:
            return ToolOutput(
                success=False,
                error=f"ఈ పథకం ({scheme_id}) కోసం స్పష్టమైన అర్హత నిబంధనలు ఇంకా నిర్వచించలేదు."
            )

        return rule_method(input_data)

    def _check_aasara_pension(self, data: EligibilityInput) -> ToolOutput:
        # Rules: Age >= 57, Income limit (simplified)
        reasons = []
        missing = []

        if data.age is None:
            missing.append("వయస్సు")
        elif data.age < 57:
            reasons.append(f"మీ వయస్సు {data.age} సంవత్సరాలు మాత్రమే, అవసరమైన కనిష్ట వయస్సు 57 సంవత్సరాలు.")

        if data.income is None:
            missing.append("కుటుంబ వార్షిక ఆదాయం")
        elif data.income > 200000: # Simplified cap
            reasons.append(f"మీ కుటుంబ ఆదాయం ₹{data.income} ఉండటం వల్ల ఆదాయ పరిమితి దాటిపోయింది.")

        if missing:
            return ToolOutput(
                success=False,
                data={"status": "MISSING_INFO", "missing_fields": missing}
            )
        
        if reasons:
            return ToolOutput(
                success=True,
                data={"status": "INELIGIBLE", "reasons": reasons}
            )

        return ToolOutput(
            success=True,
            data={
                "status": "ELIGIBLE",
                "message": "మీ వివరాల ప్రకారం మీరు ఆసరా పెన్షన్‌కు అర్హులు కావచ్చు."
            }
        )

    def _check_rythu_bandhu(self, data: EligibilityInput) -> ToolOutput:
        # Rules: Must own land
        if data.land_acres is None:
            return ToolOutput(
                success=False,
                data={
                    "status": "MISSING_INFO",
                    "missing_fields": ["వ్యవసాయ భూమి ఎకరాలు"]
                }
            )
        
        if data.land_acres <= 0:
            return ToolOutput(
                success=True,
                data={
                    "status": "INELIGIBLE",
                    "reasons": ["రైతు బంధు కోసం తప్పనిసరిగా వ్యవసాయ భూమి ఉండాలి."]
                }
            )
            
        return ToolOutput(
            success=True,
            data={
                "status": "ELIGIBLE",
                "message": f"మీరు ఉన్న {data.land_acres} ఎకరాల భూమిపై రైతు బంధు సాయం పొందే అవకాశం ఉంది."
            }
        )
