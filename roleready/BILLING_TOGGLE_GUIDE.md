# Billing Toggle Guide for RoleReady

## 🎯 Overview

This guide explains how to easily toggle billing enforcement on/off for RoleReady during the beta phase and beyond.

## 🔧 Current Status: Billing DISABLED (Beta Mode)

RoleReady is currently running in **Public Beta** mode with:
- ✅ All features free and unlimited
- ✅ No payment enforcement
- ✅ Usage tracking for analytics
- ✅ Beta branding in UI

## 🚀 How to Toggle Billing

### Method 1: Environment Variable (Recommended)

Set the environment variable to control billing:

```bash
# Disable billing (Beta mode)
export ROLEREADY_BILLING_ENABLED=false

# Enable billing (Production mode)
export ROLEREADY_BILLING_ENABLED=true
```

### Method 2: Configuration File

Edit `roleready/apps/api/roleready_api/core/billing_config.py`:

```python
class BillingConfig:
    # Change this line to toggle billing
    BILLING_ENABLED = False  # Beta mode (all free)
    # BILLING_ENABLED = True   # Production mode (enforce limits)
```

### Method 3: Database Configuration (Future)

For production, you can store billing configuration in the database:

```sql
-- Create a system configuration table
CREATE TABLE public.system_config (
  key text PRIMARY KEY,
  value text NOT NULL,
  updated_at timestamptz DEFAULT now()
);

-- Insert billing toggle
INSERT INTO public.system_config (key, value) 
VALUES ('billing_enabled', 'false');
```

## 📊 What Changes When Billing is Enabled

### Backend Changes
- ✅ Feature access checks become enforced
- ✅ Usage limits are applied
- ✅ API endpoints return proper error codes (402 Payment Required)
- ✅ Subscription validation is active

### Frontend Changes
- ✅ Plan limits are displayed
- ✅ Upgrade prompts appear
- ✅ Usage meters show remaining quota
- ✅ Beta banner is hidden

### Database Changes
- ✅ Subscription table is actively used
- ✅ Feature usage is tracked and limited
- ✅ Billing events are logged

## 🎨 UI Changes

### Beta Mode (Current)
```jsx
// Beta banner shows
<BetaBanner /> // "🟢 RoleReady Public Beta - Free access"

// Plan status shows
<PlanStatus /> // "Public Beta — Free access (no limits)"

// All features show as unlimited
"Unlimited access to all features"
```

### Production Mode (When Enabled)
```jsx
// Beta banner hidden
// Plan status shows actual limits
<PlanStatus /> // "Free Plan - 5 resumes, 3 rewrites"

// Feature cards show limits
"5 of 5 resumes used this month"
"Upgrade for unlimited access"
```

## 🔄 Migration Steps

### Step 1: Enable Billing
1. Set `ROLEREADY_BILLING_ENABLED=true`
2. Restart the API server
3. Update frontend to remove beta messaging
4. Test feature limits

### Step 2: Configure Plans
1. Update plan configurations in `billing_config.py`
2. Set appropriate limits for each plan
3. Configure pricing tiers
4. Test upgrade flows

### Step 3: Stripe Integration
1. Add Stripe webhook endpoints
2. Configure payment processing
3. Set up subscription management
4. Test payment flows

### Step 4: User Communication
1. Send email to existing users
2. Announce pricing changes
3. Provide migration path
4. Set grace period for current users

## 📈 Usage Analytics During Beta

Even with billing disabled, the system tracks usage for:

### Analytics Data
- Feature usage patterns
- User engagement metrics
- Popular features
- Performance bottlenecks

### Pricing Decisions
- Usage frequency by feature
- User behavior patterns
- Feature adoption rates
- Optimal pricing tiers

### Example Analytics Queries
```sql
-- Most used features
SELECT feature_name, SUM(usage_count) as total_usage
FROM public.feature_usage
WHERE created_at >= now() - interval '30 days'
GROUP BY feature_name
ORDER BY total_usage DESC;

-- User engagement
SELECT 
  COUNT(DISTINCT user_id) as active_users,
  AVG(usage_count) as avg_usage_per_user
FROM public.feature_usage
WHERE created_at >= now() - interval '7 days';
```

## 🛡️ Safety Features

### Graceful Degradation
- Users with existing subscriptions continue working
- Beta users get automatic free tier
- No data loss during transition

### Rollback Plan
- Easy to disable billing if issues arise
- Database rollback procedures
- Feature flag controls

### Monitoring
- Usage tracking continues during beta
- Performance monitoring
- Error rate tracking

## 📋 Checklist for Billing Activation

### Pre-Activation
- [ ] Usage analytics collected for 30+ days
- [ ] Pricing strategy finalized
- [ ] Payment processor configured
- [ ] Legal terms updated
- [ ] Support documentation ready

### Activation Day
- [ ] Set `ROLEREADY_BILLING_ENABLED=true`
- [ ] Deploy updated configuration
- [ ] Monitor system performance
- [ ] Send user notifications
- [ ] Update marketing materials

### Post-Activation
- [ ] Monitor conversion rates
- [ ] Track support tickets
- [ ] Analyze user feedback
- [ ] Adjust pricing if needed
- [ ] Optimize upgrade flows

## 🎯 Benefits of This Approach

### During Beta
- ✅ Focus on product quality
- ✅ Gather user feedback
- ✅ Build usage analytics
- ✅ Establish market fit
- ✅ No payment friction

### When Ready to Monetize
- ✅ Instant billing activation
- ✅ No code refactoring needed
- ✅ Existing user data preserved
- ✅ Smooth transition experience
- ✅ Data-driven pricing decisions

## 🔮 Future Enhancements

### Advanced Features
- A/B testing for pricing
- Dynamic pricing based on usage
- Enterprise custom pricing
- Usage-based billing models

### Integration Options
- Multiple payment processors
- Subscription management platforms
- Revenue recognition systems
- Tax calculation services

---

## 📞 Support

For questions about billing configuration:
- Check the configuration files
- Review the API documentation
- Test in staging environment first
- Monitor logs after changes

**Remember: The billing system is designed to be easily toggled without breaking existing functionality. Users will always have a smooth experience regardless of billing status.**
