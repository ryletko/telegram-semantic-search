<template>
	<div class="p-4 h-full overflow-y-auto" ref="scrollContainer" @scroll="handleScroll">
		<div v-if="!importId" class="text-center py-4">Please select a conversation to view its history</div>
		<div v-else-if="loading && messages.length === 0" class="text-center py-4">Loading messages...</div>
		<div v-else-if="messages.length === 0" class="text-center py-4">No messages found</div>
		<div v-else>
			<!-- Loading indicator for older messages -->
			<div :class="{ 'opacity-100': loadingOlder, 'opacity-0': !loadingOlder }" class="text-center text-gray-500 text-sm top-0 left-0 w-full">
				Loading older messages...
			</div>
			
			<div class="space-y-3">
				<div 
					v-for="message in messages" 
					:key="message.id" 
					:data-message-id="message.id"
					class="w-full mb-3 flex" 
					:class="{ 'justify-end': message.is_self, 'justify-start': !message.is_self }"
				>
					<div class="max-w-[70%] bg-white rounded-lg p-3 shadow">
						<div class="flex justify-between mb-1 text-sm">
							<strong>{{ message.from_name }}</strong>
							<span class="ml-6 text-gray-600">{{ formatDate(message.date) }}</span>
						</div>
						<div class="whitespace-pre-wrap break-words">{{ message.text }}</div>
					</div>
				</div>
			</div>
			
			<!-- Loading indicator for newer messages -->
			<div v-if="loadingNewer" class="text-center py-2 text-gray-500 text-sm">
				Loading newer messages...
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, onMounted, PropType, watch } from "vue";
import { HistoryMessage } from "../types";
import { formatDate } from "../common/stringFormat";

const props = defineProps({
	importId: {
		type: String as PropType<string | null>,
		required: true,
		default: null,
	},
	messageId: {
		type: Number as PropType<number | null>,
		required: true,
		default: null,
	},
});

const messages = ref<HistoryMessage[]>([]);
const loading = ref(false);
const loadingOlder = ref(false);
const loadingNewer = ref(false);
const scrollContainer = ref<HTMLElement | null>(null);
const limit = 200; // Number of messages to fetch per request
const scrollThreshold = 200; // Pixels from top/bottom to trigger loading more

// Track min and max message IDs for pagination
const minMessageId = ref<number | null>(null);
const maxMessageId = ref<number | null>(null);

// Watch for changes in importId or messageId to reload messages
watch([() => props.importId, () => props.messageId], () => {
	// Reset state and load messages when props change
	messages.value = [];
	minMessageId.value = null;
	maxMessageId.value = null;
	loadMessages();
});

onMounted(async () => {
	loadMessages();
});

async function loadMessages() {
	if (!props.importId) return;
	
	try {
		loading.value = true;
		const response = await fetch(`/api/history?import_id=${props.importId}&limit=${limit}&message_id=${props.messageId || ''}`);
		if (!response.ok) {
			throw new Error("Failed to fetch history");
		}
		const data = await response.json();
		messages.value = data.messages || [];
		
		// Update min and max message IDs
		if (messages.value.length > 0) {
			updateMessageIdBoundaries();
		}
	} catch (error) {
		console.error("Error fetching history:", error);
	} finally {
		loading.value = false;
	}
}

function updateMessageIdBoundaries() {
	if (messages.value.length === 0) return;
	
	const messageIds = messages.value.map(msg => msg.id);
	minMessageId.value = Math.min(...messageIds);
	maxMessageId.value = Math.max(...messageIds);
}

async function loadOlderMessages() {
	if (!props.importId || !minMessageId.value || loading.value || loadingOlder.value) return;
	
	try {
		loadingOlder.value = true;
		
		// Save reference to a specific message element before loading new messages
		let referenceMessageId: number | null = null;
		if (messages.value.length > 0) {
			// Use the first visible message as reference point
			referenceMessageId = findFirstVisibleMessageId();
		}
		
		const response = await fetch(`/api/history?import_id=${props.importId}&limit=${limit}&message_id=${minMessageId.value - limit}`);
		if (!response.ok) {
			throw new Error("Failed to fetch older messages");
		}
		
		const data = await response.json();
		const olderMessages = data.messages || [];
		
		if (olderMessages.length > 0) {
			// Filter out any duplicates
			const existingIds = new Set(messages.value.map((msg: HistoryMessage) => msg.id));
			const newMessages = olderMessages.filter((msg: HistoryMessage) => !existingIds.has(msg.id));
			
			// Store current scroll position and height
			const prevScrollHeight = scrollContainer.value?.scrollHeight || 0;
			
			// Prepend new messages
			messages.value = [...newMessages, ...messages.value];
			
			// Update min message ID
			updateMessageIdBoundaries();
			
			setTimeout(() => {
				// Restore scroll position after DOM update
				const newScrollHeight = scrollContainer.value?.scrollHeight || 0;
				const heightDifference = newScrollHeight - prevScrollHeight;
				scrollContainer.value!.scrollTop += heightDifference;
			}, 1);
		}
	} catch (error) {
		console.error("Error fetching older messages:", error);
	} finally {
		loadingOlder.value = false;
	}
}

function findFirstVisibleMessageId(): number | null {
	if (!scrollContainer.value || messages.value.length === 0) return null;
	
	const containerTop = scrollContainer.value.scrollTop;
	const messageElements = scrollContainer.value.querySelectorAll('[data-message-id]');
	
	for (let i = 0; i < messageElements.length; i++) {
		const element = messageElements[i] as HTMLElement;
		const rect = element.getBoundingClientRect();
		const containerRect = scrollContainer.value.getBoundingClientRect();
		
		// Check if this message is visible in the viewport
		if (rect.top >= containerRect.top && rect.top <= containerRect.bottom) {
			return parseInt(element.dataset.messageId || '0', 10);
		}
	}
	
	return null;
}

function scrollToMessageById(messageId: number): void {
	if (!scrollContainer.value) return;
	
	// Find the message element by its data attribute
	const messageElement = scrollContainer.value.querySelector(`[data-message-id="${messageId}"]`) as HTMLElement;
	
	if (messageElement) {
		// Scroll the message into view
		messageElement.scrollIntoView({ block: 'start', behavior: 'auto' });
	}
}

async function loadNewerMessages() {
	if (!props.importId || !maxMessageId.value || loading.value || loadingNewer.value) return;
	
	try {
		loadingNewer.value = true;
		const response = await fetch(`/api/history?import_id=${props.importId}&limit=${limit}&message_id=${maxMessageId.value + 1}`);
		if (!response.ok) {
			throw new Error("Failed to fetch newer messages");
		}
		
		const data = await response.json();
		const newerMessages = data.messages || [];
		
		if (newerMessages.length > 0) {
			// Filter out any duplicates
			const existingIds = new Set(messages.value.map((msg: HistoryMessage) => msg.id));
			const newMessages = newerMessages.filter((msg: HistoryMessage) => !existingIds.has(msg.id));
			
			// Append new messages
			messages.value = [...messages.value, ...newMessages];
			
			// Update max message ID
			updateMessageIdBoundaries();
		}
	} catch (error) {
		console.error("Error fetching newer messages:", error);
	} finally {
		loadingNewer.value = false;
	}
}

function handleScroll(event: Event) {
	if (!scrollContainer.value) return;
	
	const { scrollTop, scrollHeight, clientHeight } = scrollContainer.value;
	
	// Load older messages when scrolling to the top
	if (scrollTop < scrollThreshold && !loadingOlder.value && !loading.value) {
		loadOlderMessages();
	}
	
	// Load newer messages when scrolling to the bottom
	if (scrollHeight - scrollTop - clientHeight < scrollThreshold && !loadingNewer.value && !loading.value) {
		loadNewerMessages();
	}
}
</script>
