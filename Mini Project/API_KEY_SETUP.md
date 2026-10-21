# API Key Setup Guide

This application uses OpenAI API for the CLIPS Query feature. To use this feature, you need to set up your OpenAI API key securely using environment variables.

## Quick Setup

### Option 1: Using .env file (Recommended)

1. Create a `.env` file in the `backend` directory:
   ```bash
   cd backend
   touch .env
   ```

2. Add your API key to the `.env` file:
   ```
   CLIPS_API_KEY=sk-your-openai-api-key-here
   ```

3. The application will automatically load the `.env` file when it starts.

### Option 2: Using Environment Variable (Linux/macOS)

```bash
export CLIPS_API_KEY='sk-your-openai-api-key-here'
```

### Option 3: Using Environment Variable (Windows)

```cmd
set CLIPS_API_KEY=sk-your-openai-api-key-here
```

Or in PowerShell:
```powershell
$env:CLIPS_API_KEY='sk-your-openai-api-key-here'
```

## Getting Your OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (it starts with `sk-`)
5. Add it to your `.env` file or export it as an environment variable

## Alternative Environment Variable Names

The application also accepts:
- `OPENAI_API_KEY` (alternative to `CLIPS_API_KEY`)

## Security Notes

- ✅ **DO**: Use environment variables or `.env` file
- ✅ **DO**: Add `.env` to `.gitignore` (already done)
- ❌ **DON'T**: Commit your API key to git
- ❌ **DON'T**: Hard-code API keys in source code

## Verifying Setup

After setting up your API key, restart the backend server. You should see:
- If API key is set: Application starts normally
- If API key is missing: Warning message (CLIPS Query won't work, but other features will)

## Testing

1. Start the backend server
2. Upload and analyze videos
3. Try the CLIPS Query feature
4. If you see "CLIPS Query feature is not available", check that your API key is set correctly

