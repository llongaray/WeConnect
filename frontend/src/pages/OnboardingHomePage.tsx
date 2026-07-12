import HomePresentation from '@/components/home/HomePresentation'
import TotpSetupBanner from '@/components/home/TotpSetupBanner'

export default function OnboardingHomePage() {
  return (
    <div className="space-y-4">
      <TotpSetupBanner />
      <HomePresentation />
    </div>
  )
}
