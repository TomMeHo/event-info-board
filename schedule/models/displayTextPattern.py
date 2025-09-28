from django.db import models

class DisplayTextPattern(models.Model):
    displayText = models.CharField(max_length=200)

    external_competition_name = models.CharField(max_length=200, blank=True)
    external_competition_category = models.CharField(max_length=200, blank=True)

    def __str__(self) -> str:
        return f"{self.external_competition_name}/{self.external_competition_category}"
    
    @staticmethod
    def getDisplayText(external_competition_name: str, external_competition_category: str) -> str:

        try:
            pattern = DisplayTextPattern.objects.get(
                external_competition_name=external_competition_name,
                external_competition_category=external_competition_category
            )
        except:
            
            pattern = DisplayTextPattern.objects.get(
                external_competition_name=external_competition_name
            )

        if pattern is not None:
            return pattern.displayText
        
        return "not found"