# CRO Library — Schema de données complète

## Vue d'ensemble

Ce document définit la structure de données exacte pour chaque type d'entrée dans la CRO Library. Utiliser ce schema pour :
- Créer de nouvelles entrées (manuellement ou automatiquement)
- Valider la complétude des données
- Queryifier et filtrer la library
- Exporter/importer des entrées

---

## 1. TEMPLATE LIBRARY SCHEMA

### Structure complète d'une entrée Template

```yaml
template:
  # Identifiant unique et métadonnées de base
  id: "tpl_[type]_[sector]_[variant]_[number]"
    # Format: tpl_lp_saas_freemium_001
    # Types: lp (landing page), home, product, pricing, about, blog, other
    # Sector: saas, ecom, leadgen, b2b, service, app, other
    # Variant: descriptive slug (freemium, checkout, problem_aware, etc.)
    # Number: sequential

  name: "descriptive name" # "SaaS LP — Freemium Conversion"
  description: "One-sentence value proposition of this template" # max 150 chars

  # Classement et contexte
  template_type: "Landing Page | Home Page | Product Page | Pricing Page | Other"
  page_category: "e-commerce | lead-gen | saas | advertorial | sales-page | listicle | quiz | vsl | squeeze | webinar | challenge | comparison | bundle | other"

  sector: "saas"
  subsector: "project-management" # be specific
  business_models_target:
    - "B2B SaaS"
    - "Freemium"

  # Dattes et statut
  date_added: "2024-01-15"
  date_last_modified: "2024-03-10"
  status: "active" # active | testing | archived | deprecated
  visibility: "production" # production | internal_reference | research

  # Source de création
  source:
    type: "auto-generated" # auto-generated | manual-curation | external-research
    origin: "GSG generation for [Client Name]" # détails
    original_client: "Client Name or 'Internal'"
    audit_reference: "tear_id_123 if from audit"

  # Tags et classification
  tags:
    - "freemium"
    - "low-friction"
    - "lead-magnet"
    - "form-light"
    - "product-aware"
  target_audience_awareness:
    - "Problem-Aware" # Schwartz levels: Unaware, Problem-Aware, Solution-Aware, Product-Aware, Most-Aware
    - "Solution-Aware"

  # Performance scores
  evaluation:
    cro_score: 28 # /30
    design_score: 13 # /15
    psychology_score: 4 # /6
    total_score: 45 # /51

    score_breakdown:
      cro:
        - criterion: "Headline Effectiveness"
          score: 3
          notes: "Strong hook, benefit-focused"
        - criterion: "Value Prop Clarity"
          score: 3
          notes: "Immediately clear without jargon"
        # ... 28 criteria from audit grid
      design:
        - criterion: "Visual Hierarchy"
          score: 3
          notes: "Clear eye path, strong focal points"
        # ... 15 criteria
      psychology:
        - criterion: "Social Proof"
          score: 1
          notes: "Only logos, could have testimonials"

    confidence_level: "high" # high | medium | low
    scoring_date: "2024-01-15"
    scorer_notes: "Strong CRO execution, design slightly conservative for sector"

  # Contenu et structure
  structure:
    sections:
      - order: 1
        name: "Hero"
        objective: "Grab attention, communicate value proposition"
        cro_score: 3
        elements:
          - type: "Headline"
            copy: "[template text — replace with actual]"
            emotion: "curiosity + clarity"
          - type: "Subheadline"
            copy: "[template text]"
          - type: "CTA"
            text: "Start Free Trial"
            type: "button"

      - order: 2
        name: "Problem Statement"
        objective: "Attune audience to their pain"
        cro_score: 3
        elements:
          - type: "Headline"
            copy: "Your team wastes 15 hours/week on manual task tracking"
          - type: "Problem bullets"
            count: 3

      - order: 3
        name: "Solution & How It Works"
        objective: "Show mechanism and ease of use"
        cro_score: 2.5
        elements:
          - type: "3-step visual walkthrough"
          - type: "Feature explanation"

      - order: 4
        name: "Social Proof"
        objective: "Build credibility"
        cro_score: 2
        elements:
          - type: "Logo carousel"
            company_count: 8
          - type: "Single featured testimonial"

      - order: 5
        name: "FAQ"
        objective: "Address objections"
        cro_score: 2.5
        elements:
          - type: "Accordion"
            questions: 5

      - order: 6
        name: "Final CTA"
        objective: "Convert"
        cro_score: 3
        elements:
          - type: "Button + promise"
            text: "Get Started — 14 Days Free"
            color: "primary"

  copy_framework: "PAS" # AIDA, PASTOR, BAB, StoryBrand, FAB, 4P, Custom
  copy_tone: "professional-approachable" # formal | casual | urgent | trustworthy | playful | expert

  # Design & Branding
  design:
    palette:
      primary: "#2563EB"
      secondary: "#7C3AED"
      accent: "#F59E0B"
      background: "#FFFFFF"
      text_dark: "#1F2937"
      text_light: "#6B7280"
      cta: "#2563EB"
      cta_hover: "#1E40AF"

    typography:
      heading_font: "Inter" # font family
      heading_size_h1: "48px" # @desktop
      heading_size_h1_mobile: "32px"
      heading_line_height: "1.2"
      heading_weight: "700"

      body_font: "Inter"
      body_size: "16px"
      body_line_height: "1.5"
      body_weight: "400"

    design_approach: "minimal" # minimal | maximal | brutalist | editorial | playful | luxe
    design_system_reference: "arctic-frost" # link to theme-factory or internal design system
    ambient_register: "modern-minimalist" # from Design Engine: modern-minimalist | brutalist-tech | organic-warmth | luxury-premium | playful-energetic | nature-inspired | editorial-authority | dynamic-performance

    responsive_breakpoints:
      mobile: "375px"
      tablet: "768px"
      desktop: "1440px"

    visual_assets:
      hero_image_required: true
      hero_image_type: "product-screenshot | lifestyle | abstract | video"
      features_video: true
      product_images: true
      icon_style: "outlined | filled | duotone"

  # Contenu détaillé (snippets pour référence)
  content_snippets:
    h1: "Manage your team's work in minutes, not hours"
    tagline: "Freemium project management for teams that move fast"
    primary_cta: "Start Your 14-Day Free Trial"

    problem_statement: |
      "Every team manager knows the pain: spreadsheets don't scale,
      dedicated tools cost too much, and your team wastes hours in
      status meetings nobody wants to attend."

    how_it_works: |
      "1. Add your team in seconds
      2. Create tasks and assign them instantly
      3. Watch your team's productivity soar"

    key_benefits:
      - "Never miss a deadline with smart notifications"
      - "Collaborate in real-time without context switching"
      - "Scale your workflow as your team grows"

  # Performance et résultats
  performance:
    lift_estimated:
      low: 10 # percent
      high: 20
      confidence: "medium" # high | medium | low
      basis: "internal-benchmarks" # internal-benchmarks | a-b-test | client-data | industry-research

    production_data: # if this template has been used in production
      used_count: 3 # how many projects have used this
      average_conversion_rate: null # if measured
      revenue_impact: null
      notes: "Used for 3 SaaS clients in Q1 2024, 2 of 3 above target conversion"

    historical_performance:
      - client: "Client A"
        date: "2024-01-15"
        conversion_rate: "8.5%"
        benchmark: "industry avg 5.2%"
        result: "success"

      - client: "Client B"
        date: "2024-02-20"
        conversion_rate: "6.2%"
        benchmark: "target 7%"
        result: "needs-improvement"

  # Recommandations d'usage
  recommendations:
    ideal_sectors:
      - "B2B SaaS"
      - "Project Management"
      - "Productivity Tools"

    NOT_ideal_sectors:
      - "E-commerce"
      - "Ultra-luxury"
      - "Highly regulated (Finance/Healthcare)"

    ideal_audience_awareness:
      - "Problem-Aware"
      - "Solution-Aware"

    NOT_ideal_audience_awareness:
      - "Unaware" # needs different approach

    budget_level: "medium-to-high" # low | medium | high (ad spend to justify template)

    team_sophistication: "high" # low | medium | high (internal capability to adapt)

    frequency_of_use: "seasonal" # always-relevant | seasonal | project-specific | niche

    customization_effort: "medium" # low | medium | high

    complementary_patterns:
      - "pat_testimonials_video_001"
      - "pat_faq_accordion_001"

    avoid_with_patterns:
      - "pat_hero_emotion_001" # too much emotion, conflicts with professional tone

  # Assets et fichiers
  assets:
    html_file_path: "/mnt/Mathis - Stratégie CRO Interne - Growth Society/skills/cro-library/templates/tpl_lp_saas_freemium_001.html"
    css_variables: true # CSS variables for theming

    screenshots:
      desktop_full: "/path/to/screenshot_desktop.png"
      mobile_fold: "/path/to/screenshot_mobile_fold.png"
      mobile_full: "/path/to/screenshot_mobile_full.png"

    images:
      - filename: "hero-placeholder.jpg"
        recommended_dimensions: "800x600"
        alt_text: "Product dashboard showing task management interface"
        source: "internal | unsplash | pexels | placeholder"

    fonts_used:
      - "Inter" # sourced from Google Fonts
      - name: "Custom Font"
        file: "/path/to/font.woff2"

    dependencies:
      - "Google Fonts"
      - "No external JS libraries required"

  # Variantes et relations
  variants:
    - template_id: "tpl_lp_saas_freemium_002"
      description: "Alternative hero design for more playful tone"
      difference: "Hero section completely redesigned, same copy + structure"
      when_to_use: "If audience is younger/more casual"

    - template_id: "tpl_lp_saas_freemium_001b"
      description: "Video hero variant"
      difference: "Hero image replaced with embedded video"
      when_to_use: "When product screenshots are not compelling enough"

  # Provenance et validité
  validation:
    created_by: "Claude (GSG)"
    validated_by: "Human reviewer"
    validation_date: "2024-01-16"
    validation_notes: "Strong CRO execution, approved for production use"

    client_feedback:
      - date: "2024-02-15"
        feedback: "Very strong conversion rate, but had to simplify copy for our market"
        satisfaction: "high"

    is_production_ready: true

  # Notes et contexte
  notes: "This template is particularly strong in low-friction form design and psychological clarity. Use as baseline for any SaaS freemium model."

  deprecated: false
  deprecation_reason: null
  replacement_template_id: null
```

---

## 2. PATTERN LIBRARY SCHEMA

### Structure complète d'une entrée Pattern

```yaml
pattern:
  # Identifiant unique
  id: "pat_[category]_[variant]_[number]"
    # Format: pat_hero_value_001
    # Categories: hero, cta-block, pricing, testimonials, faq, trust-signals, feature-showcase, footer-cta, navigation, social-proof, other

  name: "descriptive name"
  description: "One-sentence description"

  # Classification
  category: "Hero" # Primary bucket
  subcategory: "Problem-Aware Opener" # More specific

  sector_effectiveness:
    - sector: "SaaS"
      confidence: "high" # high | medium | low
    - sector: "Lead Gen"
      confidence: "medium"

  audience_awareness_target: "Problem-Aware" # Schwartz level

  # Dates et statut
  date_added: "2024-01-15"
  status: "active" # active | testing | archived

  # Source
  source:
    type: "auto-extracted" # auto-extracted | manual-curation
    origin: "audit of [competitor]" # ou "GSG generation [date]"
    extraction_method: "automatic-from-score" # automatic-from-score | manual-observation

  # Tags
  tags:
    - "high-converting"
    - "low-friction"
    - "problem-focused"
    - "mobile-optimized"

  # Scores
  evaluation:
    design_score: 3 # /3
    cro_score: 2.5 # /3 if applicable to category
    psychology_score: 3 # /3 if applicable

    maturity: "excellent" # experimental | good | excellent

    scoring_notes: "Strong visual hierarchy, excellent attention capture"

  # Design et Code
  design:
    layout_type: "full-width-with-asymmetry" # grid | asymmetric | card | full-width | etc.
    height_desktop: "600px"
    height_mobile: "100vh"

    colors:
      background: "white"
      text: "#1F2937"
      accent: "#2563EB"

    typography:
      heading_font: "Inter"
      heading_size: "48px"
      body_font: "Inter"
      body_size: "16px"

    visual_elements:
      - type: "image"
        position: "left"
        size: "50% width"
      - type: "headline"
        size: "48px"
        weight: "700"
      - type: "subheadline"
        size: "20px"
        weight: "400"
      - type: "cta-button"
        style: "primary"

  animations: false # or describe animations
  responsiveness:
    mobile_friendly: true
    tablet_optimized: true
    stacks_on_mobile: true

  code:
    html_snippet: |
      <section class="hero">
        <div class="hero-content">
          <h1>Your biggest problem right now</h1>
          <p>This solution directly addresses the pain you feel</p>
          <button class="cta-primary">Get Started</button>
        </div>
      </section>

    css_scope: |
      .hero {
        padding: 3rem;
        background: linear-gradient(to right, #FFFFFF, #F9FAFB);
      }
      .hero h1 {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 1rem;
      }

    js_required: false

    dependencies:
      - "Google Fonts (optional)"

    browser_compatibility:
      - "Chrome (all versions)"
      - "Firefox (all versions)"
      - "Safari (iOS 12+)"
      - "Edge (all versions)"

  # Copy et contenu
  content:
    example_headline: "[Your biggest problem]: [specific pain point]"
    copy_tone: "problem-focused"

    content_structure:
      - element: "Headline"
        purpose: "Attune to problem"
        example: "You're spending $X on Y when you should be doing Z"
      - element: "Subheadline"
        purpose: "Add credibility"
        example: "Studies show 78% of teams..."
      - element: "CTA"
        purpose: "Clear action"
        example: "See How It Works"

  # Performance
  performance:
    estimated_impact:
      low: 5 # percent lift
      high: 15
      confidence: "medium"
      basis: "internal-observations"

    tested: false
    a_b_test_data: null

  # Recommandations
  usage_recommendations:
    when_to_use: |
      "Use this pattern when your audience is problem-aware but doesn't yet know
      solutions exist. This directly resonates with their pain before pivoting
      to the solution."

    when_NOT_to_use: |
      "Avoid if audience is unaware of problem (need education first) or
      most-aware (need different approach, focus on differentiation)."

    audience_types:
      - "Product-Aware"
      - "Solution-Aware"

    NOT_audience_types:
      - "Unaware"

    design_systems_compatible:
      - "modern-minimalist"
      - "brutalist-tech"

    complementary_patterns:
      - "pat_social_proof_logos_001"
      - "pat_cta_button_urgency_001"

    conflicting_patterns:
      - "pat_hero_emotion_storytelling_001"

  # Extraction et source
  extraction_details:
    extracted_from_template_id: "tpl_lp_saas_crm_001"
    extracted_from_competitor: "Acme CRM"
    extraction_date: "2024-01-20"

  # Variantes
  variants:
    - pattern_id: "pat_hero_value_001b"
      description: "More minimalist version, text-only"
      when_to_use: "When images are not available"

    - pattern_id: "pat_hero_value_002"
      description: "Emotional variant, more lifestyle-focused"
      when_to_use: "When audience motivation is emotional rather than rational"

  # Notes
  notes: |
    "This pattern is highly versatile. It works across sectors as long as
    the audience has already identified their problem. The key to making it
    work is specificity in the headline — generic problem statements perform 50% worse."

  case_studies: null # or link to actual case studies if available
```

---

## 3. RÉFÉRENCES LP SCHEMA

### Structure complète d'une entrée Référence LP

```yaml
reference_lp:
  # Identifiant unique
  id: "ref_lp_[sector]_[variant]_[number]"
    # Format: ref_lp_saas_crm_acme_001

  # Métadonnées de base
  brand_name: "Acme CRM"
  website_url: "https://www.acme.com/signup"

  # Classification
  category: "SaaS" # SaaS | E-commerce | Lead Gen | B2B | Service | App | Advertorial | Squeeze | Quiz | VSL
  subcategory: "CRM"

  # Analyse et scoring
  analysis:
    analysis_date: "2024-01-20"
    analyst: "Claude"
    analysis_depth: "complete" # quick | standard | complete | comprehensive

    cro_score: 24 # /30
    design_score: 12 # /15
    psychology_score: 4 # /6

    breakdown:
      cro:
        - criterion: "Headline"
          score: 3
          comment: "Strong, benefit-focused"
        # ... all 30 criteria
      design:
        - criterion: "Visual Hierarchy"
          score: 2
          comment: "Good but could be stronger"

  # Positioning & Strategy
  positioning:
    position_vs_market: "Premium, enterprise-focused solution"
    target_audience: "Mid-size to enterprise sales teams"
    value_prop_detected: "Unified sales platform with AI-powered insights"
    pricing_detected: "Enterprise pricing model, no visible pricing on LP"

    copy_framework_used: "AIDA" # inferred from structure
    copy_tone: "professional-authoritative"

  # Design Analysis
  design_analysis:
    palette:
      primary: "#1E40AF"
      secondary: "#7C3AED"
      extracted: true

    typography:
      heading: "Montserrat"
      body: "Open Sans"

    style: "corporate-professional"
    ambient_register: "luxury-premium"

    key_visual_elements:
      - "Hero video (product demo)"
      - "Feature comparison matrix"
      - "Customer logos carousel"
      - "Testimonial cards"

  # Strengths
  strengths:
    cro:
      - "Excellent headline that communicates value immediately"
      - "Strong social proof with recognizable logos"
      - "Clear case study section with metrics"

    design:
      - "Professional color palette, well-executed"
      - "Good use of video in hero"
      - "Clean typography hierarchy"

    psychology:
      - "Strong authority signals (enterprise focus)"
      - "Scarcity implied but not overt"

  # Weaknesses
  weaknesses:
    cro:
      - "Pricing not transparent (enterprise model implies high barrier)"
      - "Long form makes it harder for cold audience to scan"
      - "Form too long (5 fields) — high friction"

    design:
      - "Hero could be more visually distinctive"
      - "Too much text on desktop hero section"

    psychology:
      - "Limited emotional resonance, very rational"
      - "No urgency/scarcity signals"

  # Competitive Intelligence
  competitive_intel:
    table_stakes:
      - "Must show customer logos"
      - "Must include case study or ROI metrics"
      - "Must have professional design"

    differentiation_opportunities:
      - "Emphasize ease of implementation vs enterprise competitors"
      - "Target SMB market with transparent pricing"
      - "Simplify form for cold traffic"

    gaps_vs_competitors:
      - "No clear ROI calculator"
      - "No free trial offer"
      - "No strong urgency signal"

    innovations_detected:
      - "AI-powered insights angle is somewhat unique in market"

  # Sectorial Intelligence
  sectorial_insights:
    market_maturity: "mature" # nascent | growing | mature | saturated
    audience_consciousness: "Solution-Aware to Product-Aware"
    typical_buyer_journey: "Long sales cycle, multiple stakeholders"
    trust_building_approach: "Enterprise logos, case studies, ROI proof"

  # Screenshots et Assets
  assets:
    screenshot_full_desktop: "/path/to/screenshot.png"
    screenshot_mobile_fold: "/path/to/mobile.png"

    extracted_palette: true
    extracted_typography: true

  # Tags et Classification
  tags:
    - "enterprise-focused"
    - "logo-heavy"
    - "case-study-driven"
    - "high-friction-form"
    - "good-example" # or "bad-example"

  reference_type: "good-example" # good-example | bad-example | sectoral-benchmark | inspiration

  learning_label: "Bon exemple" # or "Mauvais exemple"

  learning_notes: |
    "Excellent execution of enterprise positioning. Shows how to build trust
    through logos and case studies. However, this approach may not work for
    SMB audience. High form friction is deliberate (qualification) but limits
    cold traffic efficiency."

  # Intégration avec library
  library_integration:
    extracted_patterns:
      - "pat_social_proof_logos_001"
      - "pat_testimonial_featured_001"
      - "pat_form_enterprise_001"

    related_templates:
      - "tpl_lp_saas_enterprise_001"

    related_teardowns:
      - "tear_acme_crm_001"

  # Métadonnées de viabilité
  viability:
    still_active: true
    last_verified: "2024-03-15"
    accessibility: "publicly-accessible"

    estimated_traffic: 50000 # monthly approx
    traffic_source: "Semrush estimate"

  # Notes
  notes: |
    "This reference is useful for understanding enterprise SaaS positioning.
    However, be aware that this approach is sector-specific and may not apply
    to consumer or SMB segments."
```

---

## 4. TEARDOWNS SCHEMA

### Structure complète d'une entrée Teardown

```yaml
teardown:
  # Identifiant unique
  id: "tear_[competitor]_[sector]_[number]"
    # Format: tear_acme_saas_crm_001

  # Métadonnées de base
  competitor_name: "Acme CRM"
  website_url: "https://www.acme.com"
  page_url: "https://www.acme.com/signup" # specific page audited

  # Contexte d'audit
  audit_context:
    audit_type: "competitive" # competitive | organic | market-research
    audit_date: "2024-01-20"
    auditor: "Claude (Growth Audit skill)"

    sector: "SaaS"
    subsector: "CRM"
    business_model: "B2B SaaS"
    estimated_arr: "$50M+" # if known

  # Positionnement détecté
  positioning:
    position_statement: "Enterprise CRM with AI-powered sales insights"
    target_market: "Mid-size to enterprise sales teams"
    target_company_size: "100+ employees"
    target_budget: "enterprise-budget"

    unique_positioning: "AI-powered analytics" # what they claim differentiates them

    go_to_market_strategy: "Direct sales, high-touch enterprise"
    pricing_strategy: "Enterprise (custom pricing)"

    value_prop_breakdown:
      primary: "Unified platform for sales management"
      secondary: "AI-powered insights for deal acceleration"
      tertiary: "Enterprise-grade security and compliance"

  # CRO Analysis (30 criteria)
  cro_analysis:
    total_score: 24 # /30

    criteria_breakdown:
      1:
        criterion: "Headline effectiveness"
        score: 3
        evidence: "Strong benefit-focused headline, immediately clear"
        reference_score: 120 # baseline benchmark
      2:
        criterion: "Value proposition clarity"
        score: 3
        evidence: "Clear differentiator, benefits explained quickly"
      3:
        criterion: "Social proof quality"
        score: 2.5
        evidence: "Multiple logos shown, but no numbers or testimonials"
      # ... continue for all 30 criteria from Growth Audit grid

    strongest_sections:
      - section: "Hero section"
        score: 3
        strength: "Immediately communicates value and differentiator"
      - section: "Customer logos"
        score: 2.5
        strength: "Recognizable enterprise brands build trust"
      - section: "Case study"
        score: 3
        strength: "Quantified results with timeline"

    weakest_sections:
      - section: "Form field"
        score: 1
        weakness: "5 fields is high friction for cold traffic"
      - section: "Pricing clarity"
        score: 0.5
        weakness: "No pricing shown, discourages price-sensitive prospects"
      - section: "Urgency/scarcity"
        score: 1
        weakness: "No urgency signals, no time-limited offers"

  # Design Analysis (15 criteria)
  design_analysis:
    total_score: 12 # /15

    criteria_breakdown:
      1:
        criterion: "Visual hierarchy"
        score: 2
        evidence: "Clear but conventional layout"
      2:
        criterion: "Color psychology"
        score: 2.5
        evidence: "Professional palette, conveys enterprise trustworthiness"
      # ... continue for all 15 criteria

    palette_analysis:
      primary: "#1E40AF"
      secondary: "#7C3AED"
      background: "#FFFFFF"
      psychology: "Professional, trustworthy, premium"

    typography_analysis:
      heading_font: "Montserrat"
      heading_assessment: "Professional, slightly corporate"
      body_font: "Open Sans"
      body_assessment: "Highly readable, standard"

    visual_distinctiveness: "Medium" # Low | Medium | High
      comment: "Professional but not particularly distinctive. Follows conventions."

    responsive_quality: "High"
      mobile_experience: "Good, stacks cleanly"

    animation_usage: "None" # or describe

  # Psychology Analysis (6 criteria)
  psychology_analysis:
    total_score: 4 # /6

    cialdini_principles:
      social_proof:
        used: true
        strength: "high" # weak | medium | high
        implementation: "Customer logos, case study metrics"

      authority:
        used: true
        strength: "high"
        implementation: "Enterprise positioning, secure/compliant messaging"

      scarcity:
        used: false
        potential: "high"
        recommendation: "Could add 'limited spots' or timeline pressure"

      reciprocity:
        used: false
        potential: "medium"
        recommendation: "Could offer free trial or resource"

      urgency:
        used: false
        strength: "low"
        recommendation: "Implied high barrier, but no explicit urgency"

      consistency:
        used: true
        strength: "medium"
        implementation: "Brand consistency throughout, but generic"

    cognitive_biases_targeted:
      - bias: "Status quo bias"
        approach: "Social proof + case study showing change is successful"
      - bias: "Loss aversion"
        approach: "Implicitly: 'competitors are using this, you might fall behind'"

  # Competitive Strategic Insights
  strategic_insights:
    table_stakes_in_market:
      - "Enterprise logo presence is mandatory"
      - "Case study with quantified ROI is expected"
      - "Professional, polished design is baseline"
      - "Security/compliance messaging is essential"

    angles_this_competitor_exploits:
      - "AI-powered insights (somewhat novel angle)"
      - "Enterprise-ready positioning"
      - "Seamless integration with existing tools"

    angles_NOT_exploited:
      - "Ease of implementation"
      - "Affordability / SMB market"
      - "Speed of deployment"
      - "Customer support quality"

    positioning_opportunities_vs_this_competitor:
      - "If you're SMB-focused: emphasize affordability + quick deployment"
      - "If you're in same enterprise space: differentiate on ease or support"
      - "If horizontal: position on flexibility vs Acme's rigid enterprise model"

    predicted_weaknesses:
      - "Long sales cycle limits growth"
      - "High pricing limits addressable market"
      - "Enterprise focus may miss SMB explosion"
      - "No free trial limits conversion velocity"

  # Extracted Patterns & Intelligence
  patterns_extracted:
    - pattern_id: "pat_hero_enterprise_001"
      pattern_name: "Enterprise Hero with logo + tagline"
      strength_level: "high"
      extraction_confidence: "high"

    - pattern_id: "pat_social_proof_logos_enterprise_001"
      pattern_name: "Logo carousel with customer count"
      strength_level: "high"

    - pattern_id: "pat_testimonial_featured_001"
      pattern_name: "Single featured testimonial with metrics"
      strength_level: "high"

    - pattern_id: "pat_form_enterprise_001"
      pattern_name: "5-field form with qualification questions"
      strength_level: "medium-high"
      note: "High friction, but intentional for lead qualification"

  # Sectorial Intelligence Contribution
  sectorial_intelligence:
    market_trends:
      - "Enterprise CRM market heavily emphasizes AI now"
      - "Customer logo integration is table stakes"
      - "Pricing transparency is low (enterprise models)"

    audience_evolution:
      - "Buyers are increasingly solution-aware in this space"
      - "Security/compliance is moving from differentiator to table stake"

    copy_evolution:
      - "AI-powered is trending heavily"
      - "Team collaboration angle diminishing"

    design_evolution:
      - "Minimalism dominating"
      - "Video content increasingly expected"
      - "Dark mode appearing but not dominant"

  # Strategic Recommendations
  recommendations_vs_this_competitor:
    top_3_features_to_emphasize: |
      1. Easier/faster implementation than enterprise solutions
      2. Transparent pricing (contrast with Acme's "contact sales")
      3. Superior customer support / success team

    predicted_market_weakness: |
      "Acme's enterprise focus leaves SMB and startup markets underserved.
      Positioning a solution for smaller teams with transparent pricing and
      quick deployment would capture significant TAM Acme is ignoring."

    copy_angles_for_differentiation:
      - "We're the enterprise CRM that doesn't cost like one"
      - "AI-powered insights without the enterprise complexity"
      - "Sales team ready in 24 hours, not 24 weeks"

  # Historical Tracking (if re-audited)
  historical_tracking:
    previous_teardown_id: null # if exists
    last_audited: "2024-01-20"
    changes_since_last_audit: null
    evolution_timeline: null

  # Tags et Classification
  tags:
    - "enterprise-focused"
    - "high-friction-form"
    - "logo-heavy"
    - "case-study-driven"

  audit_quality: "complete" # quick | standard | complete

  # Integration avec library
  library_integration:
    reference_lp_created: true
    reference_lp_id: "ref_lp_saas_crm_acme_001"

    related_templates: []
    related_teardowns: [] # similar competitors

  # Notes
  notes: |
    "Acme CRM is a well-executed enterprise play. Their positioning,
    design, and messaging are all professional and appropriate for their
    target market. However, this approach is very sector/segment specific.
    The high friction and enterprise focus work for them but would fail
    for a SMB-focused product.

    Key learnings: Enterprise buyers value logo credibility and case studies.
    Consumer/SMB buyers value affordability and speed. Very different playbooks."

  # Audit Metadata
  audit_metadata:
    audit_completed: true
    validation_status: "verified"
    notes_for_next_auditor: "This company pivoted pricing model in Q4 2023. Check for landing page changes in next audit."
```

---

## 5. SECTORIAL AGGREGATION & INDEXING

### Comment les données sont organisées par secteur

```
LIBRARY INDEX
├── BY SECTOR
│   ├── SaaS
│   │   ├── CRM
│   │   │   ├── Templates [tpl_lp_saas_crm_001, tpl_lp_saas_crm_002]
│   │   │   ├── Patterns [pat_hero_value_001, pat_social_proof_logos_001]
│   │   │   ├── References [ref_lp_saas_crm_acme_001, ref_lp_saas_crm_salesforce_001]
│   │   │   └── Teardowns [tear_acme_crm_001, tear_hubspot_crm_001]
│   │   │
│   │   ├── Project Management
│   │   │   ├── Templates [...]
│   │   │   ├── Patterns [...]
│   │   │   └── ...
│   │
│   ├── E-commerce
│   │   ├── Fashion
│   │   ├── Electronics
│   │   └── ...
│   │
│   └── [Other sectors]
│
├── BY PATTERN CATEGORY
│   ├── Hero
│   │   ├── Problem-Aware variants
│   │   ├── Value-Prop variants
│   │   ├── Emotion variants
│   │   └── [Other variants]
│   │
│   ├── CTA Block
│   │   ├── Button only
│   │   ├── Form variants
│   │   └── [Other variants]
│   │
│   └── [Other categories]
│
└── BY PERFORMANCE
    ├── Top Performers (score ≥2.5/3)
    ├── Solid Performers (score 1.5-2.4/3)
    ├── Learning Samples (score <1.5/3)
    └── Experimental (untested)
```

---

## 6. QUERY INTERFACE

### Comment chercher efficacement dans la library

```
SEARCH QUERIES

Simple text search:
- "SaaS hero pattern" → returns all hero patterns tagged with SaaS

Advanced structured search:
- Category: Hero
- Sector: SaaS
- SubSector: CRM
- Audience Awareness: Problem-Aware
- Min Score: 2.0/3.0
- Sort By: Score DESC
- Limit: 5 results

Field-specific searches:
- tags: "high-converting"
- performance:estimated_impact > 10
- source.type: "auto-generated"
- status: "active"

Sector Intelligence Query:
- sector: "SaaS"
- subsector: "CRM"
- Return: {templates[], patterns[], teardowns[], copy_angles[], design_trends[], common_objections[]}
```

---

## 7. DATA VALIDATION RULES

Chaque entrée doit passer ces validations :

```
VALIDATION CHECKLIST

TEMPLATE:
□ Unique ID following naming convention
□ Name and description provided
□ Sector and subsector specified
□ Score /51 calculated
□ At least 3 sections documented
□ HTML file exists and is valid
□ At least one screenshot provided
□ Source clearly documented
□ Status is one of: active | testing | archived | deprecated
□ If status = archived, replacement_template_id provided

PATTERN:
□ Unique ID following naming convention
□ Category and subcategory specified
□ Design score provided (/3)
□ HTML snippet is valid and scoped
□ At least one use case documented
□ Source clearly documented
□ Mobile friendliness verified
□ At least one screenshot/visual provided

REFERENCE LP:
□ Unique ID following naming convention
□ URL is valid and accessible
□ Category specified
□ Analysis date provided
□ At least CRO score provided
□ At least 2 strengths and 2 weaknesses documented
□ At least 1 competitive insight provided
□ Screenshot captured

TEARDOWN:
□ Unique ID following naming convention
□ Competitor name and URL specified
□ Sector specified
□ Audit date provided
□ All 30 CRO criteria scored
□ Audit quality level specified
□ At least 3 strategic insights provided
□ Patterns extracted and linked
```

---

## 8. VERSIONING & MAINTENANCE

```
LIBRARY VERSION: 1.0

Last Sync: [auto-updated after each operation]

Data Integrity Checks (run monthly):
- Duplicate detection (same URL in multiple entries)
- Broken links (HTML files, screenshots)
- Orphaned entries (patterns from deleted templates)
- Score outliers (entries with unusually high/low scores)
- Stale entries (last accessed > 6 months ago)

Archival Policy:
- Templates unused > 9 months → review for archival
- Patterns unused > 12 months → review for archival
- References invalid URLs → mark as archived
- Teardowns > 18 months old → keep for history, mark as archived

Mutation Tracking:
- All updates logged with timestamp, reason, operator
- Version history maintained (can revert if needed)
```

---

## 9. EXPORT & INTEGRATION FORMATS

### Format pour export vers GSG

```json
{
  "templates": [
    {
      "id": "tpl_lp_saas_crm_001",
      "name": "SaaS CRM LP — Freemium",
      "html": "...",
      "sectors": ["SaaS", "CRM"],
      "audience_awareness": ["Problem-Aware"],
      "score": 125,
      "lift_estimated": {"low": 10, "high": 20}
    }
  ],
  "patterns": [
    {
      "id": "pat_hero_value_001",
      "name": "Problem-Aware Hero",
      "html_snippet": "...",
      "category": "Hero",
      "score": 2.8,
      "sectors": ["SaaS"]
    }
  ]
}
```

### Format pour export vers Growth Audit

```json
{
  "benchmarks": {
    "sector": "SaaS",
    "subsector": "CRM",
    "avg_cro_score": 23.5,
    "avg_design_score": 12.1,
    "templates_count": 8,
    "patterns_count": 24,
    "teardowns_count": 5
  },
  "table_stakes": [
    "Customer logos required",
    "Case study with metrics required",
    "Professional design baseline"
  ],
  "gaps": [
    "No competitor emphasizes SMB affordability"
  ]
}
```
