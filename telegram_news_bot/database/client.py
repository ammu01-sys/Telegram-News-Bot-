from supabase import create_client, Client
from ..utils.config import SUPABASE_URL, SUPABASE_KEY

# Initialize Supabase client using the official SDK.
# The client provides methods for interacting with the Supabase REST API.
# No connection pool or psycopg2 is used.

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)