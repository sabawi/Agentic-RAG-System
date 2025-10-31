"""
Feature Flags Configuration

Controls rollout of enhanced features for the Agentic-RAG System.

All flags default to False (disabled) for safety.
Enable only after thorough testing.
"""

import logging

logger = logging.getLogger(__name__)


class FeatureFlags:
    """
    Feature flags for enhanced capabilities.

    All flags default to False (disabled) for safety.
    Enable features progressively after testing.
    """

    # ========================================================================
    # ENHANCED DATA COLLECTION FEATURES
    # ========================================================================

    # SEC EDGAR Integration (from ENHANCED_DATA_COLLECTION_IMPLEMENTATION_PLAN.md)
    ENABLE_SEC_EDGAR = False
    SEC_EDGAR_CACHE_ENABLED = True  # Caching always enabled when feature is on

    # Academic Research APIs (from ENHANCED_DATA_COLLECTION_IMPLEMENTATION_PLAN.md)
    ENABLE_ACADEMIC_RESEARCH = False
    ACADEMIC_RESEARCH_SEMANTIC_SCHOLAR = True  # Individual source toggles
    ACADEMIC_RESEARCH_ARXIV = True
    ACADEMIC_RESEARCH_PUBMED = True

    # Enhanced RSS Processing (from ENHANCED_DATA_COLLECTION_IMPLEMENTATION_PLAN.md)
    ENABLE_ENHANCED_RSS = False
    ENHANCED_RSS_GOOGLE_NEWS = True
    ENHANCED_RSS_CONTENT_EXTRACTION = True
    ENHANCED_RSS_SENTIMENT_ANALYSIS = True

    # ========================================================================
    # FUNDAMENTAL ANALYSIS & DCF FEATURES
    # ========================================================================

    # Detailed Financial Analysis (from FUNDAMENTAL_ANALYSIS_DCF_IMPLEMENTATION_PLAN.md)
    ENABLE_DETAILED_ANALYSIS = True  # ✅ ENABLED for testing
    DETAILED_ANALYSIS_FINANCIAL_STATEMENTS = True
    DETAILED_ANALYSIS_FINANCIAL_RATIOS = True
    DETAILED_ANALYSIS_DCF_VALUATION = True
    DETAILED_ANALYSIS_PROJECTIONS = True

    # ========================================================================
    # CONTROL METHODS
    # ========================================================================

    @classmethod
    def enable_all_data_collection(cls):
        """Enable all data collection features (use with caution!)."""
        cls.ENABLE_SEC_EDGAR = True
        cls.ENABLE_ACADEMIC_RESEARCH = True
        cls.ENABLE_ENHANCED_RSS = True
        logger.warning("⚠️ All data collection features enabled")

    @classmethod
    def enable_all_financial_analysis(cls):
        """Enable all financial analysis features (use with caution!)."""
        cls.ENABLE_DETAILED_ANALYSIS = True
        logger.warning("⚠️ All financial analysis features enabled")

    @classmethod
    def enable_all(cls):
        """Enable ALL features (use with extreme caution!)."""
        cls.enable_all_data_collection()
        cls.enable_all_financial_analysis()
        logger.critical("🚨 ALL FEATURES ENABLED - Use in staging only!")

    @classmethod
    def disable_all(cls):
        """Emergency rollback - disable all enhancements."""
        cls.ENABLE_SEC_EDGAR = False
        cls.ENABLE_ACADEMIC_RESEARCH = False
        cls.ENABLE_ENHANCED_RSS = False
        cls.ENABLE_DETAILED_ANALYSIS = False
        logger.critical("🚨 EMERGENCY ROLLBACK: All enhancements disabled")

    @classmethod
    def get_status(cls) -> dict:
        """Get current feature flag status."""
        return {
            'data_collection': {
                'sec_edgar': cls.ENABLE_SEC_EDGAR,
                'academic_research': cls.ENABLE_ACADEMIC_RESEARCH,
                'enhanced_rss': cls.ENABLE_ENHANCED_RSS,
            },
            'financial_analysis': {
                'detailed_analysis': cls.ENABLE_DETAILED_ANALYSIS,
                'financial_statements': cls.DETAILED_ANALYSIS_FINANCIAL_STATEMENTS,
                'financial_ratios': cls.DETAILED_ANALYSIS_FINANCIAL_RATIOS,
                'dcf_valuation': cls.DETAILED_ANALYSIS_DCF_VALUATION,
                'projections': cls.DETAILED_ANALYSIS_PROJECTIONS,
            }
        }

    @classmethod
    def log_status(cls):
        """Log current feature flag status."""
        status = cls.get_status()
        logger.info("Feature Flags Status:")
        logger.info(f"  Data Collection: {status['data_collection']}")
        logger.info(f"  Financial Analysis: {status['financial_analysis']}")


# Initialize logging on import
FeatureFlags.log_status()
