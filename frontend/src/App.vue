<template>
	<div class="flex flex-col h-screen">
		<!-- Main App -->
		<div class="flex flex-col h-full">
			<!-- Header -->
			<header class="bg-indigo-900 text-white flex justify-between items-center p-4">
				<h1 class="text-xl font-bold">Telegram Semantic Search</h1>
				<button
					v-if="currentView === 'history'"
					@click="currentView = 'search'"
					class="px-4 py-2 rounded transition-colors bg-white bg-opacity-10 hover:bg-opacity-20"
				>
					Back to Search
				</button>
			</header>

			<!-- Main Content with Sidebar -->
			<div class="flex flex-1 overflow-hidden">
				<!-- Imports Sidebar -->
				<div class="w-64 bg-white border-r border-gray-200 flex flex-col">
					<h2 class="p-4 m-0 border-b border-gray-200 font-medium">Imported Chats</h2>

					<div v-if="imports.length === 0" class="p-4 text-gray-600 text-center">No chats imported yet</div>

					<div v-else class="overflow-y-auto flex-1">
						<div
							v-for="import_ in imports"
							:key="import_.import_id"
							class="p-3 border-b border-gray-100 cursor-pointer hover:bg-gray-50"
							:class="{ 'bg-blue-50 border-l-4 border-l-blue-500': selectedImport && selectedImport.import_id === import_.import_id }"
							@click="selectImport(import_)"
						>
							<div class="font-bold">{{ import_.chat_name }}</div>
							<div class="text-xs text-gray-600 mt-1">{{ formatDate(import_.timestamp) }}</div>
						</div>
					</div>

					<!-- Import Button Section -->
					<div class="p-4 mt-auto border-t border-gray-200">
						<input type="file" id="import-file" accept=".json" class="hidden" @change="handleFileUpload" ref="fileInput" />
						<button
							@click="triggerFileInput"
							class="w-full flex items-center justify-center py-2 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded transition-colors"
							:disabled="importLoading"
						>
							<svg v-if="!importLoading" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
								/>
							</svg>
							<svg v-if="importLoading" class="animate-spin h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
								<path
									class="opacity-75"
									fill="currentColor"
									d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
								></path>
							</svg>
							{{ importLoading ? "Importing..." : "Import Chat JSON" }}
						</button>

						<div v-if="importSuccess" class="mt-2 p-2 bg-green-100 text-green-800 text-sm rounded">Import successful!</div>

						<div v-if="importError" class="mt-2 p-2 bg-red-100 text-red-800 text-sm rounded">
							{{ importError }}
						</div>
					</div>
				</div>

				<!-- Main Content Area -->
				<div class="flex-1 overflow-hidden">
					<SearchView 
						v-if="currentView === 'search'" 
						:selectedImport="selectedImport" 
						:initialQuery="searchQuery"
						:initialResults="searchResults"
						:initialHasSearched="hasSearched"
						@view-history="viewHistory"
						@update-search-state="updateSearchState"
					/>
					<HistoryView v-else-if="currentView === 'history'" :importId="historyImportId" :messageId="historyMessageId" />
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import SearchView from "./components/SearchView.vue";
import HistoryView from "./components/HistoryView.vue";
import { formatDate } from "./common/stringFormat";

interface Import {
	import_id: string;
	chat_name: string;
	chat_id: string;
	processed_count: number;
	model_name: string;
	timestamp: string;
}

interface SearchResult {
	id: number;
	import_id: string;
	from_name: string;
	text: string;
	date: string;
	similarity: number;
}

// View management
const currentView = ref("search");
const historyImportId = ref<string | null>(null);
const historyMessageId = ref<number | null>(null);

// Search state to preserve between views
const searchQuery = ref("");
const searchResults = ref<SearchResult[]>([]);
const hasSearched = ref(false);

// Imports management
const imports = ref<Import[]>([]);
const selectedImport = ref<Import | null>(null);

// Import functionality
const fileInput = ref<HTMLInputElement | null>(null);
const importLoading = ref(false);
const importSuccess = ref(false);
const importError = ref("");


function selectImport(import_: Import) {
	selectedImport.value = import_;
	searchQuery.value = "";
	searchResults.value = [];
	hasSearched.value = false;
}

function viewHistory(import_id: string, message_id: number) {
	historyImportId.value = import_id;
	historyMessageId.value = message_id;
	currentView.value = "history";
}

function updateSearchState(query: string, results: SearchResult[], searched: boolean) {
	searchQuery.value = query;
	searchResults.value = results;
	hasSearched.value = searched;
}

function triggerFileInput() {
	fileInput.value?.click();
}

function loadImportsFromStorage() {
	const storedImports = localStorage.getItem("telegram_imports");
	if (storedImports) {
		imports.value = JSON.parse(storedImports);
	}
}

function saveImportsToStorage() {
	localStorage.setItem("telegram_imports", JSON.stringify(imports.value));
}

async function handleFileUpload(event: Event) {
	const target = event.target as HTMLInputElement;
	if (!target.files?.length) return;

	const file = target.files[0];
	const formData = new FormData();
	formData.append("file", file);

	importLoading.value = true;
	importSuccess.value = false;
	importError.value = "";

	try {
		const response = await fetch("/api/import", {
			method: "POST",
			body: formData,
		});

		const data = await response.json();

		if (response.ok) {
			// Add timestamp to import data
			const newImport: Import = {
				import_id: data.import.import_id,
				chat_name: data.import.chat_name,
				chat_id: data.import.chat_id,
				processed_count: data.import.processed_count,
				model_name: data.import.model_name,
				timestamp: data.import.timestamp,
			};

			// Add to imports list
			imports.value.unshift(newImport);
			saveImportsToStorage();

			importSuccess.value = true;
			selectedImport.value = newImport;
		} else {
			importError.value = data.error || "Import failed";
		}
	} catch (error) {
		console.error("Import failed:", error);
		importError.value = "Import failed. Please try again.";
	} finally {
		importLoading.value = false;
		// Reset file input
		if (fileInput.value) fileInput.value.value = "";
	}
}

// Initial load
onMounted(() => {
	loadImportsFromStorage();
});
</script>

<style>
html,
body {
	height: 100%;
	margin: 0;
	font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

[v-cloak] {
	display: none;
}

.fade-enter-active,
.fade-leave-active {
	transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
	opacity: 0;
}
</style>
