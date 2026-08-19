from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')

checks = []
def require(path: str, needles: list[str], label: str):
    text = read(path)
    missing = [n for n in needles if n not in text]
    checks.append((label, missing))

require('frontend/src/feature/templates/components/TemplateWizard.tsx', ['beforeunload', 'Save as Draft', 'Leave Without Saving'], 'BUG-11 unsaved template protection')
require('backend/src/modules/auth/application/usecases/core/verify_and_enable_totp_usecase.py', ['valid_window=1'], 'BUG-12 TOTP drift window')
require('backend/src/modules/auth/application/usecases/core/login_user_usecase.py', ['_create_2fa_challenge', 'oauth_login', 'requires_2fa'], 'BUG-13 shared MFA challenge')
require('backend/src/modules/auth/domain/enums/user_activity_enums.py', ['TWO_FA_CHALLENGE'], 'BUG-13 MFA challenge audit')
require('frontend/src/routes/verify-2fa.tsx', ['Use recovery code', 'Use authenticator code'], 'BUG-13 recovery-code mode')
require('backend/src/modules/auth/presentation/routers/auth_oauth_routers.py', ['requires_2fa', '/verify-2fa'], 'BUG-13 OAuth MFA redirect')
require('frontend/src/feature/contacts/components/ContactsDashboard.tsx', ['Delete Collection', 'Select all', 'all matching'], 'BUG-14 collections/select-all')
require('frontend/src/shared/components/AppSelect.tsx', ['placement', 'top-auto', 'bottom-full'], 'BUG-25 dropup select')
require('frontend/src/shared/components/PaginationControls.tsx', ['placement="top"'], 'BUG-15/25 shared pagination select')
require('frontend/src/feature/organization/components/team/MembersTable.tsx', ['lg:overflow-x-visible'], 'BUG-16 desktop horizontal scrollbar')
require('backend/src/modules/organization/application/usecases/core/invite_organization_member_usecase.py', ['already exists in this organization', 'already pending'], 'BUG-19 invitation duplicate handling')
require('frontend/src/feature/organization/components/team/InvitePanel.tsx', ['showToast', 'Invitation sent successfully'], 'BUG-19 invitation toast feedback')
require('frontend/src/routes/__root.tsx', ['top-4', 'right-4'], 'BUG-20 top-right toast host')
require('frontend/src/shared/hooks/useToast.ts', ['toasts', 'slice(-4)'], 'BUG-20 toast stacking')
require('frontend/src/index.css', ['bg-stone-50', 'text-stone-900', 'mt-support-hero'], 'BUG-17 semantic dark-mode contrast')
require('frontend/src/feature/organization/components/account-settings/SecuritySettings.tsx', ['global top-right toast host'], 'BUG-20 no local security toast')
require('backend/src/modules/organization/application/usecases/core/list_organization_members_usecase.py', ['presence', 'last_active_at'], 'BUG-21 server presence')
require('frontend/src/feature/organization/hooks/useMembers.ts', ['refetchInterval'], 'BUG-21 presence polling')
require('backend/src/modules/auth/application/usecases/core/register_user_usecase.py', ['requires_login'], 'BUG-22 registration requires login')
require('backend/src/modules/auth/presentation/routers/auth_core_routers.py', ['requires_login'], 'BUG-22 signup no session cookie')
require('frontend/src/feature/campaigns/components/CampaignScheduleStep.tsx', ['batchSizeInput'], 'BUG-23 natural numeric editing')
require('backend/src/modules/auth/presentation/routers/auth_password_routers.py', ['/forgot/verify-code', '/forgot/reset'], 'BUG-24 split reset endpoints')
require('frontend/src/routes/ForgotPassword/verify.tsx', ['Create New Password', 'reset_challenge'], 'BUG-24 split reset UI')
require('frontend/src/feature/templates/components/TemplateDetails.tsx', ['Continue to Templates'], 'BUG-18 completion action')

failed = False
for label, missing in checks:
    if missing:
        failed = True
        print(f'FAIL: {label}: missing {missing}')
    else:
        print(f'PASS: {label}')
if failed:
    sys.exit(1)
print('ALL QA BUGS 11-25 REGRESSION CHECKS PASSED')
