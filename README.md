# oss-metrics (ossm)

A Python CLI application for collecting and analyzing GitHub repository metrics.

"ossm" (pronounced "awesome") is the CLI tool that this project exposes. Run `ossm --help` for
more information about available commands.

## Features

- Collects GitHub issues and pull requests for one or more repositories
- Builds a Panel dashboard for displaying statistics that can be rendered as a static website

## Usage

### Install dependencies

Using conda:

```bash
conda env update --name th-oss-metrics -f environment.yaml
conda activate th-oss-metrics
```

### Set your GitHub token

Export your GitHub personal access token as an environment variable:

```bash
export GITHUB_TOKEN=your_github_token_here
```

### Run the CLI

To check out the available commands, run:

```bash
ossm --help
```

## Testing

Run all tests with:

```bash
pytest
```
