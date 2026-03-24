#!/usr/bin/env python
import os

from setuptools import find_packages, setup

# Читаем README.md для long_description
with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

# Читаем requirements.txt
with open("requirements.txt", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh if line.strip() and not line.startswith("#")
    ]


# Получаем версию из __init__.py
def get_version():
    init_path = os.path.join(
        os.path.dirname(__file__), "django_simple_ratings", "__init__.py"
    )
    with open(init_path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    return "0.1.0"


setup(
    name="django-simple-ratings",
    version=get_version(),
    author="Ваше Имя",
    author_email="your.email@example.com",
    description="Простая система комментариев с рейтингом для Django",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/django-simple-ratings",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/django-simple-ratings/issues",
        "Documentation": "https://github.com/yourusername/django-simple-ratings/wiki",
        "Source Code": "https://github.com/yourusername/django-simple-ratings",
    },
    classifiers=[
        # Полный список: https://pypi.org/classifiers/
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "Framework :: Django :: 4.2",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords=[
        "django",
        "ratings",
        "comments",
        "reviews",
        "stars",
        "feedback",
        "django-app",
        "django-package",
    ],
    packages=find_packages(exclude=["tests", "tests.*"]),
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.7",
    install_requires=requirements,
    # Опциональные зависимости
    extras_require={
        "dev": [
            "black>=23.0",
            "flake8>=6.0",
            "isort>=5.12",
            "pytest>=7.0",
            "pytest-django>=4.5",
            "coverage>=7.0",
            "sphinx>=7.0",
            "twine>=4.0",
        ],
        "test": [
            "pytest>=7.0",
            "pytest-django>=4.5",
            "coverage>=7.0",
        ],
        "docs": [
            "sphinx>=7.0",
            "sphinx-rtd-theme>=1.0",
        ],
    },
    # Скрипты для командной строки
    entry_points={
        "console_scripts": [
            # Можно добавить CLI утилиты
        ],
    },
    # Категория на PyPI
    classifiers_license="MIT",
)
