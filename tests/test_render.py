from render.templates import list_templates, render_template


def test_templates_exist():
    templates = list_templates()
    assert "modern" in templates
    assert "classic_two_column" in templates


def test_render_template_renders_minimal_context():
    context = {
        "contact": {"name": "Alex", "email": "alex@example.com"},
        "work_experience": [],
        "projects": [],
        "skills": ["Python"],
        "education": [],
        "certifications": [],
        "summary": "Testing render",
    }
    rendered = render_template("modern", context)
    assert "Alex" in rendered
    assert "Testing render" in rendered
