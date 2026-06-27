from core.cloud_client import CloudClient
from core.privacy_manager import PrivacyManager
from core.orchestrator import Orchestrator
from core.tenant_router import TenantRouter

router = TenantRouter(
    orchestrator=Orchestrator(
        privacy_manager=PrivacyManager(),
        cloud_client=CloudClient(provider="groq"),
        config_path="industry_profiles/template/prompts.json",
    ),
    tenants_path="industry_profiles/tenants.json",
)

result = router.run("demo_tenant", "My name is Jane Smith. What are my data rights?")
print(f"Tenant: {result.display_name}")
print(f"Profile: {result.profile_used}")
print(f"Response: {result.final_text}")