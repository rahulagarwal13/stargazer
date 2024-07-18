import requests
import matplotlib.pyplot as plt
import datetime
import re
import sys
import time
import math
import csv

def get_total_stars(repo_owner, repo_name, token):
    url = f'https://api.github.com/repos/{repo_owner}/{repo_name}'
    headers = {
        'Authorization': f'token {token}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"GitHub API request failed with status code {response.status_code}")
    data = response.json()
    return data['stargazers_count']

def fetch_stars(repo_owner, repo_name, token, total_stars):
    print(f"Fetching stars for repository: {repo_owner}/{repo_name}")
    stars = []
    page = 1
    per_page = 100
    url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/stargazers'
    headers = {
        'Accept': 'application/vnd.github.v3.star+json',
        'Authorization': f'token {token}'
    }
    
    retries = 5
    total_pages = math.ceil(total_stars / per_page)
    print(f"Total stars: {total_stars}. Fetching {total_pages} pages...")

    while page <= total_pages:
        try:
            print(f"Fetching page {page} of {total_pages}...")
            response = requests.get(url, headers=headers, params={'page': page, 'per_page': per_page})
            if response.status_code == 403:
                print("Rate limit exceeded. Retrying in 60 seconds...")
                time.sleep(60)
                continue

            if response.status_code != 200:
                raise Exception(f"GitHub API request failed with status code {response.status_code}")
            
            data = response.json()
            if not data:
                break
            
            for star in data:
                starred_at = datetime.datetime.strptime(star['starred_at'], "%Y-%m-%dT%H:%M:%SZ")
                stars.append(starred_at)
            
            page += 1
        except requests.exceptions.RequestException as e:
            if retries > 0:
                retries -= 1
                print(f"Request failed: {e}. Retrying... ({retries} retries left)")
                time.sleep(10)
            else:
                raise Exception(f"Failed to fetch stars after multiple retries: {e}")
    
    print(f"Total stars fetched: {len(stars)}")
    return stars

def save_stars_to_csv(stars, filename):
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['starred_at'])
        for star in stars:
            writer.writerow([star.isoformat()])
    print(f"Star data saved to {filename}")

def plot_stars(stars):
    print("Processing star data...")
    dates = [star.date() for star in stars]
    dates.sort()
    
    date_counts = {}
    for date in dates:
        if date in date_counts:
            date_counts[date] += 1
        else:
            date_counts[date] = 1
    
    cumulative_counts = []
    cumulative_count = 0
    for date in sorted(date_counts.keys()):
        cumulative_count += date_counts[date]
        cumulative_counts.append((date, cumulative_count))
    
    dates, counts = zip(*cumulative_counts)
    
    print("Generating chart...")
    plt.figure(figsize=(10, 5))
    plt.plot(dates, counts, label='Stars Over Time')
    plt.xlabel('Date')
    plt.ylabel('Number of Stars')
    plt.title('GitHub Repository Star History')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    print("Chart generated successfully!")

def parse_github_url(url):
    pattern = r"https://github.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)"
    match = re.match(pattern, url)
    if match:
        return match.group("owner"), match.group("repo")
    else:
        raise ValueError("Invalid GitHub URL")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python github_star_history.py <github_repository_url> <github_token>")
        sys.exit(1)

    repo_url = sys.argv[1]
    github_token = sys.argv[2]
    
    try:
        print("Parsing GitHub URL...")
        repo_owner, repo_name = parse_github_url(repo_url)
        print(f"Repository Owner: {repo_owner}, Repository Name: {repo_name}")
        
        total_stars = get_total_stars(repo_owner, repo_name, github_token)
        stars = fetch_stars(repo_owner, repo_name, github_token, total_stars)
        
        save_stars_to_csv(stars, 'stars.csv')
        plot_stars(stars)
    except ValueError as e:
        print(e)
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
