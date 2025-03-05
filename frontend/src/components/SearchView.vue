<template>
  <div class="p-6 h-full flex flex-col overflow-hidden">
    <!-- No import selected message -->
    <div v-if="!selectedImport" class="text-center text-gray-600">
      Please select a chat from the sidebar to start searching
    </div>

    <!-- Search interface -->
    <div v-else class="flex flex-col h-full overflow-hidden">
      <div class="mb-6 flex-shrink-0">
        <div class="flex gap-4">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Enter your search query..."
            class="flex-1 p-3 border border-gray-300 rounded text-base"
            @keyup.enter="search"
          />
          <button
            @click="search"
            class="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded transition-colors"
            :disabled="searching"
          >
            {{ searching ? "Searching..." : "Search" }}
          </button>
        </div>

        <div v-if="searchError" class="mt-2 p-2 bg-red-100 text-red-800 text-sm rounded">
          {{ searchError }}
        </div>
      </div>

      <!-- Search Results with overflow handling -->
      <div class="flex-1 overflow-y-auto">
        <div v-if="results.length > 0" class="space-y-4">
          <div
            v-for="result in results"
            :key="result.id"
            class="p-4 bg-white rounded-lg shadow hover:shadow-md transition-shadow cursor-pointer"
            @click="viewHistory(result.import_id, result.id)"
          >
            <div class="flex justify-between items-start mb-2">
              <div class="font-medium">{{ result.from_name }}</div>
              <div class="text-sm text-gray-600">{{ formatDate(result.date) }}</div>
            </div>
            <div class="text-gray-800">{{ result.text }}</div>
            <div class="mt-2 text-sm text-gray-500">
              Similarity: {{ (result.similarity * 100).toFixed(1) }}%
            </div>
          </div>
        </div>

        <!-- No Results Message -->
        <div v-else-if="hasSearched && !searching" class="text-center text-gray-600 mt-8">
          No messages found matching your search
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { formatDate } from '../common/stringFormat';

interface SearchResult {
  id: number;
  import_id: string;
  from_name: string;
  text: string;
  date: string;
  similarity: number;
}

const props = defineProps({
  selectedImport: {
    type: Object as () => {
      import_id: string;
      chat_name: string;
      chat_id: string;
      processed_count: number;
      model_name: string;
      timestamp: string;
    } | null,
    required: true,
    default: null
  },
  initialQuery: {
    type: String,
    default: ""
  },
  initialResults: {
    type: Array as () => SearchResult[],
    default: () => []
  },
  initialHasSearched: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits<{
  (e: "view-history", import_id: string, message_id: number): void;
  (e: "update-search-state", query: string, results: SearchResult[], hasSearched: boolean): void;
}>();

// Search state
const searchQuery = ref(props.initialQuery);
const searching = ref(false);
const searchError = ref("");
const results = ref<SearchResult[]>(props.initialResults);
const hasSearched = ref(props.initialHasSearched);

// Update parent component when search state changes
watch([searchQuery, results, hasSearched], () => {
  emit("update-search-state", searchQuery.value, results.value, hasSearched.value);
});

// Functions
function viewHistory(import_id: string, message_id: number) {
  emit("view-history", import_id, message_id);
}

async function search() {
  if (!searchQuery.value.trim() || !props.selectedImport) return;

  searching.value = true;
  searchError.value = "";
  results.value = [];

  try {
    const response = await fetch("/api/search", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: searchQuery.value,
        import_id: props.selectedImport.import_id,
        limit: 200,
        min_similarity: 0.3,
      }),
    });

    const data = await response.json();
    console.log("Search response:", data);

    if (response.ok) {
      results.value = data.results || [];
      hasSearched.value = true;
      console.log("Processed results:", results.value);
    } else {
      searchError.value = data.error || "Search failed";
    }
  } catch (error) {
    console.error("Search failed:", error);
    searchError.value = "Search failed. Please try again.";
  } finally {
    searching.value = false;
  }
}
</script>
