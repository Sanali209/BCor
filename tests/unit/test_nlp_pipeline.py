import pytest
from unittest.mock import patch
from src.modules.llm.domain.nlp_pipeline import NlpPipeline

@pytest.fixture(autouse=True)
def mock_nltk():
    with patch("src.modules.llm.domain.nlp_pipeline.nltk") as mock:
        # Mock word_tokenize to return lowercase split by space for simplicity in tests
        mock.word_tokenize.side_effect = lambda x: x.lower().replace(",", " ,").replace("!", " !").split()
        yield mock

def test_nlp_pipeline_basic_replace():
    """Test that the pipeline can replace words based on a dictionary."""
    pipeline = NlpPipeline()
    pipeline.set_text("I saw several women at the park.")
    
    # We expect 'women' to be replaced by 'woman' based on legacy dictionary
    pipeline.add_replace_rule("woman", [r"\bwomen\b"])
    
    pipeline.run()
    assert "woman" in pipeline.get_text()
    assert "women" not in pipeline.get_text()

def test_nlp_pipeline_regex_extend():
    """Test that the pipeline can extend text based on regex matches."""
    pipeline = NlpPipeline()
    pipeline.set_text("Geralt of Rivia is a witcher.")
    
    # Legacy extend_dictionary: ',ext|world|the witcher': ['geralt of rivia']
    # If 'geralt of rivia' is found, prefix with ',ext|world|the witcher|'
    pipeline.add_extend_rule(",ext|world|the witcher|", ["geralt of rivia"])
    
    pipeline.run()
    assert ",ext|world|the witcher|geralt of rivia" in pipeline.get_text()

def test_nlp_pipeline_tokenization():
    """Test that the pipeline correctly tokenizes text."""
    pipeline = NlpPipeline()
    pipeline.set_text("Hello, world!")
    pipeline.run()
    
    tokens = pipeline.get_tokens()
    assert "hello" in tokens
    assert "world" in tokens
    assert "!" in tokens
