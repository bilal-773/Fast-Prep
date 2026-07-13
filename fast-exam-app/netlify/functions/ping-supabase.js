const supabaseUrl = 'https://ykigxzsgiuejnslbdkij.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlraWd4enNnaXVlam5zbGJka2lqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODI3MTQ3MDAsImV4cCI6MjA5ODI5MDcwMH0.iq01to8HPB_0qgMxCkEozzgXQlgWcN5xqpmcYD6BaIE';

exports.handler = async (event, context) => {
  try {
    const res = await fetch(`${supabaseUrl}/rest/v1/universities?limit=1`, {
      headers: {
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`
      }
    });

    if (!res.ok) {
      throw new Error(`Supabase API responded with status ${res.status}`);
    }

    console.log('Successfully pinged Supabase database.');
    return {
      statusCode: 200,
      body: JSON.stringify({ message: 'Ping successful' })
    };
  } catch (err) {
    console.error('Failed to ping Supabase database:', err.message);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: err.message })
    };
  }
};

// Netlify configuration to run daily
exports.config = {
  schedule: '@daily'
};
